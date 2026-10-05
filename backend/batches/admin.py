from django.contrib import admin

from .models import Batch, BatchProduct


@admin.register(BatchProduct)
class BatchProductAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
        "batch_number",
        "batch_product",
        "purpose",
        "date",
        "qc_result",
        "quantity",
        "quantity_unit",
        "remaining_quantity",
        "created_by",
        "is_closed",
    )
    list_filter = ("purpose", "qc_result", "is_closed")
    search_fields = ("batch_number", "batch_product__name", "provider")
