from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsLoadingClerkOrAdmin
from catalog.models import Product

from .batch_helpers import (
    available_batches_qs,
    deduct_batch_liters,
    get_available_batch,
    serialize_batch_option,
)
from .models import BundleComposition, ReadyStockLot
from .serializers import (
    ReadyStockAddSerializer,
    ReadyStockLotSerializer,
    ReadyStockPatchSerializer,
)


def _batches_for_product(product: Product):
    """Active Esha batches for a product (requires parent brand + fill volume)."""
    if not product.batch_product_id or product.fill_volume_liters is None:
        return []
    return [
        serialize_batch_option(b)
        for b in available_batches_qs(product.batch_product_id)
    ]


class ReadyStockListCreateView(APIView):
    permission_classes = [IsLoadingClerkOrAdmin]

    def get(self, request):
        qs = ReadyStockLot.objects.select_related("product", "source_batch").all()
        search = (request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(product__name__icontains=search)
                | Q(batch_label__icontains=search)
            )
        total = qs.aggregate(total=Sum("on_hand"))["total"] or 0
        return Response(
            {
                "total_bottles": total,
                "lots": ReadyStockLotSerializer(qs, many=True).data,
            }
        )

    @transaction.atomic
    def post(self, request):
        ser = ReadyStockAddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        product = Product.objects.filter(
            pk=data["product_id"], is_active=True, show_on_sheet=True
        ).first()
        if not product:
            return Response({"detail": "Unknown sheet product."}, status=400)

        comps = list(
            BundleComposition.objects.filter(bundle_product=product)
            .select_related("component_product")
            .order_by("sort_order", "id")
        )
        updated_lots = []

        try:
            if comps:
                updated_lots.append(self._add_bundle(product, comps, data, request.user))
            else:
                updated_lots.append(self._add_plain(product, data, request.user))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(
            ReadyStockLotSerializer(updated_lots, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    def _add_plain(self, product, data, user):
        bottles = data.get("bottles")
        if not bottles or bottles < 1:
            raise ValueError("bottles must be >= 1.")
        batch_id = data.get("batch_id")
        source_batch = None
        if batch_id:
            if product.fill_volume_liters is None:
                raise ValueError(
                    f"{product.name} cannot deduct from Esha liquid "
                    f"(no fill volume). Use free-text batch."
                )
            source_batch = get_available_batch(batch_id, product)
            liters = (
                Decimal(bottles) * product.fill_volume_liters
            ).quantize(Decimal("0.001"))
            deduct_batch_liters(source_batch, liters)
            label = source_batch.batch_number
        else:
            label = (data.get("batch_label") or "").strip()
            if not label:
                raise ValueError("batch_label or batch_id is required.")

        lot, _ = ReadyStockLot.objects.get_or_create(
            product=product,
            batch_label=label,
            defaults={"on_hand": 0, "source_batch": source_batch},
        )
        if source_batch and lot.source_batch_id != source_batch.id:
            lot.source_batch = source_batch
        lot.on_hand += bottles
        lot.updated_by = user
        lot.save()
        return lot

    def _add_bundle(self, product, comps, data, user):
        sets = data.get("sets")
        if not sets or sets < 1:
            raise ValueError("Bundle requires sets >= 1.")
        components = data.get("components") or []
        by_pid = {c["product_id"]: c for c in components}
        if len(by_pid) != len(comps):
            raise ValueError("Provide a batch for each bundle component.")

        labels = []
        linked_batches = []
        for comp in comps:
            cp = comp.component_product
            entry = by_pid.get(cp.id)
            if not entry:
                raise ValueError(f"Missing batch for {cp.name}.")
            batch_id = entry.get("batch_id")
            if batch_id:
                if cp.fill_volume_liters is None:
                    raise ValueError(
                        f"{cp.name} has no fill volume — use free-text batch."
                    )
                batch = get_available_batch(batch_id, cp)
                liters = (
                    Decimal(sets)
                    * Decimal(comp.qty_per_set)
                    * cp.fill_volume_liters
                ).quantize(Decimal("0.001"))
                deduct_batch_liters(batch, liters)
                labels.append(batch.batch_number)
                linked_batches.append(batch)
            else:
                label = (entry.get("batch_label") or "").strip()
                if not label:
                    raise ValueError(f"Missing batch for {cp.name}.")
                labels.append(label)
                linked_batches.append(None)

        batch_label = labels[0] if len(labels) == 1 else " + ".join(labels)
        if len(batch_label) > 64:
            raise ValueError("Combined batch label is too long.")

        source_batch = None
        if len(linked_batches) == 1 and linked_batches[0] is not None:
            source_batch = linked_batches[0]
        elif (
            len(linked_batches) > 1
            and all(b is not None for b in linked_batches)
            and len({b.id for b in linked_batches}) == 1
        ):
            source_batch = linked_batches[0]

        lot, _ = ReadyStockLot.objects.get_or_create(
            product=product,
            batch_label=batch_label,
            defaults={"on_hand": 0, "source_batch": source_batch},
        )
        if source_batch and lot.source_batch_id != source_batch.id:
            lot.source_batch = source_batch
        lot.on_hand += sets
        lot.updated_by = user
        lot.save()
        return lot


class ReadyStockDetailView(generics.UpdateAPIView):
    permission_classes = [IsLoadingClerkOrAdmin]
    serializer_class = ReadyStockPatchSerializer
    queryset = ReadyStockLot.objects.select_related("product")
    http_method_names = ["patch", "head", "options"]

    def patch(self, request, *args, **kwargs):
        lot = self.get_object()
        ser = ReadyStockPatchSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if "on_hand" in data:
            lot.on_hand = data["on_hand"]
        if "batch_label" in data:
            label = data["batch_label"].strip()
            if not label:
                return Response({"detail": "batch_label cannot be empty."}, status=400)
            conflict = (
                ReadyStockLot.objects.filter(product=lot.product, batch_label=label)
                .exclude(pk=lot.pk)
                .exists()
            )
            if conflict:
                return Response(
                    {"detail": "That batch label already exists for this product."},
                    status=400,
                )
            lot.batch_label = label
        lot.updated_by = request.user
        lot.save()
        return Response(ReadyStockLotSerializer(lot).data)


class ReadyStockFormMetaView(APIView):
    permission_classes = [IsLoadingClerkOrAdmin]

    def get(self, request):
        products = Product.objects.filter(
            is_active=True, show_on_sheet=True
        ).order_by("sort_order", "name")
        comps = BundleComposition.objects.select_related(
            "bundle_product", "component_product"
        ).order_by("bundle_product_id", "sort_order", "id")
        by_bundle = {}
        for c in comps:
            by_bundle.setdefault(c.bundle_product_id, []).append(
                {
                    "product_id": c.component_product_id,
                    "product_name": c.component_product.name,
                    "qty_per_set": c.qty_per_set,
                    "fill_volume_liters": (
                        str(c.component_product.fill_volume_liters)
                        if c.component_product.fill_volume_liters is not None
                        else None
                    ),
                    "available_batches": _batches_for_product(c.component_product),
                }
            )
        return Response(
            {
                "products": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "unit_label": p.unit_label,
                        "is_bundle": p.id in by_bundle,
                        "fill_volume_liters": (
                            str(p.fill_volume_liters)
                            if p.fill_volume_liters is not None
                            else None
                        ),
                        "available_batches": _batches_for_product(p),
                        "components": by_bundle.get(p.id, []),
                    }
                    for p in products
                ]
            }
        )


class ReadyStockBatchesView(APIView):
    permission_classes = [IsLoadingClerkOrAdmin]

    def get(self, request):
        product_id = request.query_params.get("product_id")
        if not product_id:
            return Response({"detail": "product_id is required."}, status=400)
        product = Product.objects.filter(pk=product_id, is_active=True).first()
        if not product:
            return Response({"detail": "Unknown product."}, status=400)
        return Response({"batches": _batches_for_product(product)})


class ReadyStockOptionsView(generics.ListAPIView):
    permission_classes = [IsLoadingClerkOrAdmin]
    serializer_class = ReadyStockLotSerializer

    def get_queryset(self):
        qs = ReadyStockLot.objects.filter(on_hand__gt=0).select_related(
            "product", "source_batch"
        )
        product_id = self.request.query_params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs
