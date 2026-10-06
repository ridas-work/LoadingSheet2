from django.contrib import admin

from .models import PackagingMaterial


@admin.register(PackagingMaterial)
class PackagingMaterialAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "material_type",
        "purchased_qty",
        "rejected_qty",
        "uip_qty",
        "is_active",
        "sort_order",
    )
    list_filter = ("material_type", "is_active")
    search_fields = ("name", "code")
    ordering = ("sort_order", "name")
