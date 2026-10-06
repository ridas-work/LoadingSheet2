from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class PackagingMaterial(models.Model):
    class MaterialType(models.TextChoices):
        BOTTLE = "bottle", "Bottle"
        LID = "lid", "Lid"
        CAP = "cap", "Cap"
        LABEL = "label", "Label"
        BOX = "box", "Box"
        PARTITION = "partition", "Partition"
        POUCH = "pouch", "Pouch"
        STICKER = "sticker", "Sticker"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200)
    code = models.SlugField(max_length=120, unique=True)
    material_type = models.CharField(
        max_length=20,
        choices=MaterialType.choices,
        blank=True,
        default=MaterialType.OTHER,
    )
    purchased_qty = models.PositiveIntegerField(default=0)
    rejected_qty = models.PositiveIntegerField(default=0)
    uip_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def balance(self) -> int:
        return max(0, self.purchased_qty - self.rejected_qty - self.uip_qty)

    def clean(self) -> None:
        if self.rejected_qty > self.purchased_qty:
            raise ValidationError(
                {"rejected_qty": "Rejected/damage cannot exceed purchased quantity."}
            )
        if self.rejected_qty + self.uip_qty > self.purchased_qty:
            raise ValidationError(
                "Rejected + UIP cannot exceed purchased quantity."
            )

    def save(self, *args, **kwargs):
        if not self.code and self.name:
            base = slugify(self.name)[:110] or "material"
            code = base
            n = 2
            while (
                PackagingMaterial.objects.filter(code=code)
                .exclude(pk=self.pk)
                .exists()
            ):
                code = f"{base}-{n}"
                n += 1
            self.code = code
        self.full_clean()
        return super().save(*args, **kwargs)
