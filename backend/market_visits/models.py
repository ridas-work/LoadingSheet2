from django.conf import settings
from django.db import models

from .columns import empty_availability, empty_facing


class MarketVisit(models.Model):
    class Status(models.TextChoices):
        IN_PROCESS = "in_process", "In process"
        SUBMITTED = "submitted", "Submitted"

    visit_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="market_visits",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.IN_PROCESS,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-visit_date", "-updated_at"]

    def __str__(self):
        return f"Market visit {self.visit_date} by {self.created_by_id}"


class MarketVisitStore(models.Model):
    visit = models.ForeignKey(
        MarketVisit,
        on_delete=models.CASCADE,
        related_name="stores",
    )
    store_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    remarks = models.TextField(blank=True)
    availability = models.JSONField(default=empty_availability)
    facing = models.JSONField(default=empty_facing)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.store_name
