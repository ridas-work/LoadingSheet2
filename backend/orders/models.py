from django.conf import settings
from django.db import models

from catalog.models import Customer, OuterBox, Product


class ContainerSize(models.TextChoices):
    AS_IN_CATALOG = "as_in_catalog", "As in catalog"
    FIVE_KG_LITRE_JAR = "5kg_litre_jar", "5 kg / litre jar"
    ONE_LITRE = "1_litre", "1 litre"
    FIVE_HUNDRED_ML = "500_ml", "500 ml"
    SEVEN_FIFTY_ML = "750_ml", "750 ml"
    TWO_FIFTY_ML = "250_ml", "250 ml"
    ONE_HUNDRED_ML = "100_ml", "100 ml"
    TWENTY_FIVE_LTR_KG_CAN = "25_ltr_kg_can", "25 Ltr/Kg Can"
    DRUM_120 = "120_drum", "120 Litre Drum"
    DRUM_150 = "150_drum", "150 Litre Drum"
    DRUM_200 = "200_drum", "200 Litre Drum"


class Order(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"

    po_number = models.CharField(max_length=128)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="orders"
    )
    city = models.CharField(max_length=128)
    deadline_date = models.DateField()
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.SUBMITTED
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PO {self.po_number} ({self.customer.name})"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    bottles = models.PositiveIntegerField()

    class Meta:
        unique_together = ("order", "product")

    @property
    def cartons(self):
        bpc = self.product.bottles_per_carton
        if bpc <= 0:
            return 0
        return self.bottles // bpc

    def __str__(self):
        return f"{self.product.name}: {self.bottles} bottles"


class CustomCarton(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="custom_cartons"
    )
    identical_count = models.PositiveIntegerField(default=1)
    label = models.CharField(max_length=255, blank=True)
    outer_box = models.ForeignKey(OuterBox, on_delete=models.PROTECT)

    def __str__(self):
        return self.label or f"Custom carton #{self.pk}"


class CustomCartonItem(models.Model):
    custom_carton = models.ForeignKey(
        CustomCarton, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    container_size = models.CharField(
        max_length=32,
        choices=ContainerSize.choices,
        default=ContainerSize.AS_IN_CATALOG,
    )
    qty = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x {self.qty}"
