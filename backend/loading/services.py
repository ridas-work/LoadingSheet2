from decimal import Decimal

from django.db import transaction
from django.db.models import Q

from batches.models import Batch
from dispatch.models import Trip
from orders.models import Order

from .models import LoadingSheetLine, ReadyStockLot


def ensure_sheet_lines_for_order(trip: Trip, order: Order) -> None:
    """Create missing structural sheet lines without wiping saved batch/weight."""
    existing = {
        (line.box_no, line.product_id): line
        for line in LoadingSheetLine.objects.filter(trip=trip, order=order)
    }
    desired: list[tuple[int, int, int, int]] = []  # box_no, product_id, bottles, sort
    box_no = 1
    sort_order = 0

    for line in order.lines.select_related("product").order_by("id"):
        bpc = line.product.bottles_per_carton
        if bpc <= 0:
            continue
        cartons = line.bottles // bpc
        for _ in range(cartons):
            desired.append((box_no, line.product_id, bpc, sort_order))
            sort_order += 1
            box_no += 1

    for carton in order.custom_cartons.prefetch_related("items").order_by("id"):
        for _ in range(carton.identical_count):
            for item in carton.items.order_by("id"):
                desired.append((box_no, item.product_id, item.qty, sort_order))
                sort_order += 1
            box_no += 1

    desired_keys = {(b, p) for b, p, _, _ in desired}
    for box, product_id, bottles, sort in desired:
        key = (box, product_id)
        if key in existing:
            row = existing[key]
            if row.bottles != bottles or row.sort_order != sort:
                row.bottles = bottles
                row.sort_order = sort
                row.save(update_fields=["bottles", "sort_order", "updated_at"])
        else:
            LoadingSheetLine.objects.create(
                trip=trip,
                order=order,
                box_no=box,
                product_id=product_id,
                bottles=bottles,
                sort_order=sort,
            )

    # Remove unassigned orphan structure rows no longer in order
    for key, row in existing.items():
        if (
            key not in desired_keys
            and row.ready_stock_lot_id is None
            and row.source_batch_id is None
            and row.carton_weight_kg is None
        ):
            row.delete()


def ensure_sheet_lines_for_trip(trip: Trip) -> None:
    for trip_order in trip.trip_orders.select_related("order").all():
        ensure_sheet_lines_for_order(trip, trip_order.order)


def progress_for_queryset(qs):
    total = qs.count()
    assigned = qs.filter(
        Q(ready_stock_lot_id__isnull=False) | Q(source_batch_id__isnull=False)
    ).count()
    return assigned, total


def reserved_bottles_by_lot(
    lot_ids=None, exclude_trip_id=None
) -> dict[int, int]:
    """Bottles/sets reserved on planned trips (not yet delivered)."""
    qs = LoadingSheetLine.objects.filter(
        ready_stock_lot_id__isnull=False,
        trip__status=Trip.Status.PLANNED,
    )
    if lot_ids is not None:
        qs = qs.filter(ready_stock_lot_id__in=lot_ids)
    if exclude_trip_id is not None:
        qs = qs.exclude(trip_id=exclude_trip_id)
    reserved: dict[int, int] = {}
    for lot_id, bottles in qs.values_list("ready_stock_lot_id", "bottles"):
        reserved[lot_id] = reserved.get(lot_id, 0) + bottles
    return reserved


def available_to_assign(on_hand: int, reserved: int) -> int:
    return max(0, on_hand - reserved)


@transaction.atomic
def deliver_trip(trip: Trip) -> Trip:
    """Mark trip delivered and deduct ready stock / Esha liters."""
    if trip.status == Trip.Status.DELIVERED:
        raise ValueError("Trip is already delivered.")
    if trip.status != Trip.Status.PLANNED:
        raise ValueError("Only planned trips can be marked delivered.")

    lines = list(
        LoadingSheetLine.objects.filter(trip=trip).select_related(
            "product", "ready_stock_lot", "source_batch"
        )
    )
    lot_deltas: dict[int, int] = {}
    batch_deltas: dict[int, Decimal] = {}

    for line in lines:
        if line.ready_stock_lot_id:
            lot_deltas[line.ready_stock_lot_id] = (
                lot_deltas.get(line.ready_stock_lot_id, 0) + line.bottles
            )
        elif line.source_batch_id and line.product.fill_volume_liters is not None:
            liters = (
                Decimal(line.bottles) * line.product.fill_volume_liters
            ).quantize(Decimal("0.001"))
            batch_deltas[line.source_batch_id] = (
                batch_deltas.get(line.source_batch_id, Decimal("0")) + liters
            )

    for lot_id, qty in lot_deltas.items():
        lot = ReadyStockLot.objects.select_for_update().get(pk=lot_id)
        lot.on_hand = max(0, lot.on_hand - qty)
        lot.save(update_fields=["on_hand", "updated_at"])

    for batch_id, liters in batch_deltas.items():
        batch = Batch.objects.select_for_update().get(pk=batch_id)
        remaining = batch.remaining_quantity - liters
        if remaining < 0:
            remaining = Decimal("0")
        batch.remaining_quantity = remaining.quantize(Decimal("0.001"))
        batch.save(update_fields=["remaining_quantity", "updated_at"])

    trip.status = Trip.Status.DELIVERED
    trip.save(update_fields=["status", "updated_at"])
    return trip
