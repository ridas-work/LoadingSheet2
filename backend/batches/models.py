from decimal import Decimal

from django.conf import settings
from django.db import models


class BatchProduct(models.Model):
    """Parent brand for filling (not bottle size SKUs)."""

    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Batch(models.Model):
    class Purpose(models.TextChoices):
        REGULAR = "regular", "Regular"
        SAMPLE = "sample", "Sample"

    class QuantityUnit(models.TextChoices):
        L = "L", "L"
        ML = "ml", "ml"

    class QCResult(models.TextChoices):
        SUCCESSFUL = "successful", "Successful"
        UNSUCCESSFUL = "unsuccessful", "Unsuccessful"

    purpose = models.CharField(max_length=16, choices=Purpose.choices)
    batch_number = models.CharField(max_length=64, unique=True)
    batch_product = models.ForeignKey(
        BatchProduct, on_delete=models.PROTECT, related_name="batches"
    )
    date = models.DateField()
    ph = models.CharField(max_length=64, blank=True)
    solids = models.CharField(max_length=128, blank=True)
    appearance = models.CharField(max_length=255, blank=True)
    provider = models.CharField(max_length=128, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    quantity_unit = models.CharField(
        max_length=8, choices=QuantityUnit.choices, default=QuantityUnit.L
    )
    remaining_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Remaining volume in liters",
    )
    customer_name = models.CharField(max_length=255, blank=True)
    qc_result = models.CharField(max_length=16, choices=QCResult.choices)
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="batches_created",
    )
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.batch_number

    @staticmethod
    def to_liters(quantity: Decimal, unit: str) -> Decimal:
        if unit == Batch.QuantityUnit.ML:
            return (quantity / Decimal("1000")).quantize(Decimal("0.001"))
        return quantity

    @property
    def is_available(self) -> bool:
        return (
            self.qc_result == self.QCResult.SUCCESSFUL
            and not self.is_closed
            and self.remaining_quantity > 0
        )
