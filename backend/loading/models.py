from django.conf import settings
from django.db import models

from catalog.models import Product
from dispatch.models import Trip
from orders.models import Order


class ReadyStockLot(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="ready_stock_lots"
    )
    batch_label = models.CharField(max_length=64)
    source_batch = models.ForeignKey(
        "batches.Batch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ready_stock_lots",
    )
    on_hand = models.PositiveIntegerField(default=0)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ready_stock_updates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product__sort_order", "product__name", "batch_label"]
        unique_together = ("product", "batch_label")

    def __str__(self) -> str:
        return f"{self.product.name} / {self.batch_label}: {self.on_hand}"


class BundleComposition(models.Model):
    bundle_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="bundle_components",
    )
    component_product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="used_in_bundles",
    )
    qty_per_set = models.PositiveIntegerField(default=1)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["bundle_product_id", "sort_order", "id"]
        unique_together = ("bundle_product", "component_product")

    def __str__(self) -> str:
        return (
            f"{self.bundle_product.name} → "
            f"{self.qty_per_set}× {self.component_product.name}"
        )


class LoadingSheetLine(models.Model):
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name="sheet_lines"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="sheet_lines"
    )
    box_no = models.PositiveIntegerField()
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    bottles = models.PositiveIntegerField()
    ready_stock_lot = models.ForeignKey(
        ReadyStockLot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sheet_lines",
    )
    source_batch = models.ForeignKey(
        "batches.Batch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sheet_lines",
    )
    carton_weight_kg = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True
    )
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order_id", "box_no", "sort_order", "id"]
        unique_together = ("trip", "order", "box_no", "product")

    def __str__(self) -> str:
        return f"Trip {self.trip_id} PO {self.order_id} box {self.box_no}"
