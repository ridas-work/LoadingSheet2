from decimal import Decimal

from batches.models import Batch
from catalog.models import Product


def available_batches_qs(batch_product_id=None):
    qs = Batch.objects.filter(
        qc_result=Batch.QCResult.SUCCESSFUL,
        is_closed=False,
        remaining_quantity__gt=0,
    ).select_related("batch_product")
    if batch_product_id:
        qs = qs.filter(batch_product_id=batch_product_id)
    return qs.order_by("-date", "-created_at")


def serialize_batch_option(batch: Batch) -> dict:
    return {
        "id": batch.id,
        "batch_number": batch.batch_number,
        "batch_product_id": batch.batch_product_id,
        "remaining_quantity": str(batch.remaining_quantity),
        "date": batch.date.isoformat(),
    }


def get_available_batch(batch_id: int, product: Product) -> Batch:
    if not product.batch_product_id:
        raise ValueError(
            f"{product.name} has no Esha parent brand — use a free-text batch."
        )
    batch = (
        available_batches_qs(product.batch_product_id).filter(pk=batch_id).first()
    )
    if not batch:
        raise ValueError(
            "Batch is not available for this product "
            "(must be successful QC with liters remaining)."
        )
    return batch


def deduct_batch_liters(batch: Batch, liters: Decimal) -> None:
    if liters <= 0:
        raise ValueError("Liters to deduct must be positive.")
    if batch.remaining_quantity < liters:
        raise ValueError(
            f"Batch {batch.batch_number} has only "
            f"{batch.remaining_quantity} L left; need {liters} L."
        )
    batch.remaining_quantity = (batch.remaining_quantity - liters).quantize(
        Decimal("0.001")
    )
    batch.save(update_fields=["remaining_quantity", "updated_at"])
