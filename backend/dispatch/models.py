from django.conf import settings
from django.db import models

from orders.models import Order


class Trip(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        DELIVERED = "delivered", "Delivered"

    vehicle_no = models.CharField(max_length=64, blank=True)
    driver_name = models.CharField(max_length=128, blank=True)
    helper_name = models.CharField(max_length=128, blank=True)
    production_incharge = models.CharField(max_length=128, blank=True)
    security = models.CharField(max_length=128, blank=True)
    default_challan_no = models.CharField(max_length=128, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="trips_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Trip #{self.pk} ({self.vehicle_no or 'no vehicle'})"


class TripOrder(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="trip_orders")
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="trip_assignment",
    )
    challan_no = models.CharField(max_length=128, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.trip_id} ← PO {self.order.po_number}"
