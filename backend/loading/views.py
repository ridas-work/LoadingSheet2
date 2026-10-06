from django.db import transaction
from django.db.models import Count, Prefetch, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsLoadingClerkOrAdmin
from batches.models import Batch
from catalog.models import WEIGHT_TOLERANCE_PCT
from dispatch.models import Trip, TripOrder
from orders.models import Order

from .batch_helpers import available_batches_qs, serialize_batch_option
from .models import LoadingSheetLine, ReadyStockLot
from .serializers import (
    LoadingSheetLineSerializer,
    LoadingTripDetailSerializer,
    LoadingTripListSerializer,
    PendingOrderSerializer,
    ReadyStockLotSerializer,
    SheetSaveSerializer,
)
from .services import (
    deliver_trip,
    ensure_sheet_lines_for_trip,
    reserved_bottles_by_lot,
)


class PendingOrderListView(generics.ListAPIView):
    """All submitted orders still to deliver (on a planned trip or not yet on any trip)."""

    permission_classes = [IsLoadingClerkOrAdmin]
    serializer_class = PendingOrderSerializer

    def get_queryset(self):
        delivered_order_ids = TripOrder.objects.filter(
            trip__status=Trip.Status.DELIVERED
        ).values_list("order_id", flat=True)
        return (
            Order.objects.filter(status=Order.Status.SUBMITTED)
            .exclude(id__in=delivered_order_ids)
            .select_related(
                "customer",
                "created_by",
                "trip_assignment",
                "trip_assignment__trip",
            )
            .annotate(
                total_products=Count("lines", distinct=True),
                total_bottles=Coalesce(Sum("lines__bottles"), Value(0)),
            )
            .order_by("deadline_date", "-created_at")
        )


class LoadingTripListView(generics.ListAPIView):
    permission_classes = [IsLoadingClerkOrAdmin]
    serializer_class = LoadingTripListSerializer

    def get_queryset(self):
        return (
            Trip.objects.filter(status=Trip.Status.PLANNED)
            .select_related("created_by")
            .prefetch_related(
                Prefetch(
                    "trip_orders",
                    queryset=TripOrder.objects.select_related("order"),
                ),
                "sheet_lines",
            )
            .order_by("-updated_at")
        )

    def list(self, request, *args, **kwargs):
        qs = list(self.get_queryset())
        for trip in qs:
            ensure_sheet_lines_for_trip(trip)
        # Refresh lines after generation
        qs = list(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class LoadingTripDetailView(generics.RetrieveAPIView):
    permission_classes = [IsLoadingClerkOrAdmin]
    serializer_class = LoadingTripDetailSerializer

    def get_queryset(self):
        return (
            Trip.objects.filter(status=Trip.Status.PLANNED)
            .select_related("created_by")
            .prefetch_related(
                Prefetch(
                    "trip_orders",
                    queryset=TripOrder.objects.select_related(
                        "order", "order__customer"
                    ),
                ),
                "sheet_lines",
            )
        )

    def retrieve(self, request, *args, **kwargs):
        trip = self.get_object()
        ensure_sheet_lines_for_trip(trip)
        serializer = self.get_serializer(trip)
        return Response(serializer.data)


class LoadingSheetView(APIView):
    permission_classes = [IsLoadingClerkOrAdmin]

    def _get_trip(self, trip_id):
        return (
            Trip.objects.filter(status=Trip.Status.PLANNED, pk=trip_id)
            .prefetch_related(
                Prefetch(
                    "trip_orders",
                    queryset=TripOrder.objects.select_related(
                        "order", "order__customer"
                    ),
                )
            )
            .first()
        )

    def get(self, request, trip_id):
        trip = self._get_trip(trip_id)
        if not trip:
            return Response({"detail": "Trip not found."}, status=404)
        ensure_sheet_lines_for_trip(trip)

        order_id = request.query_params.get("order_id")
        lines = list(
            LoadingSheetLine.objects.filter(trip=trip)
            .select_related(
                "product",
                "product__batch_product",
                "ready_stock_lot",
                "source_batch",
                "order",
                "order__customer",
            )
            .order_by("order_id", "box_no", "sort_order", "id")
        )
        if order_id:
            lines = [ln for ln in lines if str(ln.order_id) == str(order_id)]

        challan_by_order = {
            to.order_id: to.challan_no for to in trip.trip_orders.all()
        }
        product_ids = {line.product_id for line in lines}
        lots = ReadyStockLot.objects.filter(
            Q(product_id__in=product_ids, on_hand__gt=0)
            | Q(
                id__in=[
                    line.ready_stock_lot_id
                    for line in lines
                    if line.ready_stock_lot_id
                ]
            )
        ).select_related("product", "source_batch")

        parent_ids = {
            line.product.batch_product_id
            for line in lines
            if line.product.batch_product_id
            and line.product.fill_volume_liters is not None
        }
        batches_by_parent: dict[int, list] = {pid: [] for pid in parent_ids}
        if parent_ids:
            for batch in available_batches_qs().filter(batch_product_id__in=parent_ids):
                batches_by_parent.setdefault(batch.batch_product_id, []).append(
                    serialize_batch_option(batch)
                )
        # Also include already-assigned batches even if depleted
        assigned_batch_ids = [
            line.source_batch_id for line in lines if line.source_batch_id
        ]
        if assigned_batch_ids:
            for batch in Batch.objects.filter(id__in=assigned_batch_ids).select_related(
                "batch_product"
            ):
                opts = batches_by_parent.setdefault(batch.batch_product_id, [])
                if not any(o["id"] == batch.id for o in opts):
                    opts.append(serialize_batch_option(batch))

        available_batches = []
        for line in lines:
            pid = line.product.batch_product_id
            if not pid or line.product.fill_volume_liters is None:
                continue
            for opt in batches_by_parent.get(pid, []):
                available_batches.append({**opt, "product_id": line.product_id})

        # Dedupe (product_id, batch id)
        seen = set()
        deduped = []
        for opt in available_batches:
            key = (opt["product_id"], opt["id"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(opt)

        return Response(
            {
                "trip": {
                    "id": trip.id,
                    "vehicle_no": trip.vehicle_no,
                    "driver_name": trip.driver_name,
                    "default_challan_no": trip.default_challan_no,
                    "helper_name": trip.helper_name,
                    "production_incharge": trip.production_incharge,
                    "security": trip.security,
                    "status": trip.status,
                },
                "lines": LoadingSheetLineSerializer(
                    lines,
                    many=True,
                    context={"challan_by_order": challan_by_order},
                ).data,
                "available_lots": ReadyStockLotSerializer(
                    lots,
                    many=True,
                    context={"exclude_trip_id": trip.id},
                ).data,
                "available_batches": deduped,
            }
        )

    def put(self, request, trip_id):
        trip = self._get_trip(trip_id)
        if not trip:
            return Response({"detail": "Trip not found."}, status=404)
        ser = SheetSaveSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        line_ids = [item["id"] for item in ser.validated_data["lines"]]
        rows = {
            row.id: row
            for row in LoadingSheetLine.objects.filter(
                trip=trip, id__in=line_ids
            ).select_related("product", "ready_stock_lot", "source_batch")
        }
        missing = set(line_ids) - set(rows.keys())
        if missing:
            return Response(
                {"detail": f"Unknown line ids for this trip: {sorted(missing)}"},
                status=400,
            )

        lot_ids = {
            item["ready_stock_lot_id"]
            for item in ser.validated_data["lines"]
            if item.get("ready_stock_lot_id") is not None
        }
        lots = {
            lot.id: lot
            for lot in ReadyStockLot.objects.filter(id__in=lot_ids).select_related(
                "product"
            )
        }
        batch_ids = {
            item["source_batch_id"]
            for item in ser.validated_data["lines"]
            if item.get("source_batch_id") is not None
        }
        batches = {
            b.id: b
            for b in Batch.objects.filter(id__in=batch_ids).select_related(
                "batch_product"
            )
        }

        box_line_counts: dict[tuple[int, int], int] = {}
        for oid, box in LoadingSheetLine.objects.filter(trip=trip).values_list(
            "order_id", "box_no"
        ):
            key = (oid, box)
            box_line_counts[key] = box_line_counts.get(key, 0) + 1

        updated = []
        for item in ser.validated_data["lines"]:
            row = rows[item["id"]]
            has_lot = "ready_stock_lot_id" in item
            has_batch = "source_batch_id" in item
            if has_lot or has_batch:
                lot_id = item.get("ready_stock_lot_id") if has_lot else None
                batch_id = item.get("source_batch_id") if has_batch else None
                # Prefer explicit non-null; clear the other when one is set.
                if has_lot and lot_id is not None:
                    lot = lots.get(lot_id)
                    if not lot:
                        return Response(
                            {"detail": f"Unknown ready stock lot id {lot_id}."},
                            status=400,
                        )
                    if lot.product_id != row.product_id:
                        return Response(
                            {
                                "detail": (
                                    f"Lot {lot.batch_label} does not match "
                                    f"product {row.product.name}."
                                )
                            },
                            status=400,
                        )
                    row.ready_stock_lot = lot
                    row.source_batch = None
                elif has_batch and batch_id is not None:
                    batch = batches.get(batch_id)
                    if not batch:
                        return Response(
                            {"detail": f"Unknown batch id {batch_id}."},
                            status=400,
                        )
                    if (
                        not row.product.batch_product_id
                        or batch.batch_product_id != row.product.batch_product_id
                    ):
                        return Response(
                            {
                                "detail": (
                                    f"Batch {batch.batch_number} does not match "
                                    f"product {row.product.name}."
                                )
                            },
                            status=400,
                        )
                    row.source_batch = batch
                    row.ready_stock_lot = None
                else:
                    # Both null / clear assignment
                    if has_lot:
                        row.ready_stock_lot = None
                    if has_batch:
                        row.source_batch = None
            if "carton_weight_kg" in item:
                wt = item["carton_weight_kg"]
                if wt is not None:
                    product = row.product
                    std = product.standard_carton_weight_kg
                    is_full_standard = (
                        box_line_counts.get((row.order_id, row.box_no), 0) == 1
                        and row.bottles == product.bottles_per_carton
                        and std is not None
                    )
                    if is_full_standard:
                        value = float(wt)
                        std_f = float(std)
                        lo = std_f * (1 - WEIGHT_TOLERANCE_PCT / 100)
                        hi = std_f * (1 + WEIGHT_TOLERANCE_PCT / 100)
                        if value < lo or value > hi:
                            return Response(
                                {
                                    "detail": (
                                        f"Box {row.box_no} ({product.name}): "
                                        f"weight {value} kg is outside standard "
                                        f"{std_f} kg (±{WEIGHT_TOLERANCE_PCT}%). "
                                        f"Check the box."
                                    )
                                },
                                status=400,
                            )
                row.carton_weight_kg = wt
            updated.append(row)

        # Soft-reserve check: assigned on planned trips cannot exceed on_hand.
        this_trip_need: dict[int, int] = {}
        for row in updated:
            if row.ready_stock_lot_id:
                this_trip_need[row.ready_stock_lot_id] = (
                    this_trip_need.get(row.ready_stock_lot_id, 0) + row.bottles
                )
        # Include other lines on this trip not in the payload
        payload_ids = set(line_ids)
        for row in LoadingSheetLine.objects.filter(trip=trip).exclude(
            id__in=payload_ids
        ):
            if row.ready_stock_lot_id:
                this_trip_need[row.ready_stock_lot_id] = (
                    this_trip_need.get(row.ready_stock_lot_id, 0) + row.bottles
                )
        if this_trip_need:
            elsewhere = reserved_bottles_by_lot(
                lot_ids=list(this_trip_need.keys()),
                exclude_trip_id=trip.id,
            )
            check_lots = {
                lot.id: lot
                for lot in ReadyStockLot.objects.filter(id__in=this_trip_need.keys())
            }
            for lot_id, need in this_trip_need.items():
                lot = check_lots.get(lot_id) or lots.get(lot_id)
                if not lot:
                    continue
                total = elsewhere.get(lot_id, 0) + need
                if total > lot.on_hand:
                    left = max(0, lot.on_hand - elsewhere.get(lot_id, 0))
                    return Response(
                        {
                            "detail": (
                                f"Ready stock {lot.batch_label} ({lot.product.name}): "
                                f"need {need} but only {left} left to assign "
                                f"({lot.on_hand} on hand, "
                                f"{elsewhere.get(lot_id, 0)} already assigned elsewhere)."
                            )
                        },
                        status=400,
                    )

        for row in updated:
            row.save()

        challan_by_order = {
            to.order_id: to.challan_no for to in trip.trip_orders.all()
        }
        return Response(
            {
                "lines": LoadingSheetLineSerializer(
                    updated,
                    many=True,
                    context={"challan_by_order": challan_by_order},
                ).data
            }
        )


class LoadingTripDeliverView(APIView):
    permission_classes = [IsLoadingClerkOrAdmin]

    def post(self, request, trip_id):
        trip = Trip.objects.filter(pk=trip_id).first()
        if not trip:
            return Response({"detail": "Trip not found."}, status=404)
        try:
            with transaction.atomic():
                trip = deliver_trip(trip)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(
            {
                "id": trip.id,
                "status": trip.status,
                "vehicle_no": trip.vehicle_no,
            }
        )
