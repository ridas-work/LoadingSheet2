from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=255, unique=True)
    default_city = models.CharField(max_length=128, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    class UnitLabel(models.TextChoices):
        BOTTLES = "bottles", "bottles"
        BUNDLES = "bundles", "bundles"

    name = models.CharField(max_length=255, unique=True)
    bottles_per_carton = models.PositiveIntegerField(
        help_text="Units (bottles or bundles) packed per carton"
    )
    unit_label = models.CharField(
        max_length=16,
        choices=UnitLabel.choices,
        default=UnitLabel.BOTTLES,
    )
    show_on_sheet = models.BooleanField(
        default=True,
        help_text="If true, product appears on the main loading sheet",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class OuterBox(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "outer boxes"

    def __str__(self):
        return self.name
