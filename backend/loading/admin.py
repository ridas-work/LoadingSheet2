from django.contrib import admin

from .models import BundleComposition, LoadingSheetLine, ReadyStockLot


@admin.register(ReadyStockLot)
class ReadyStockLotAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "batch_label",
        "source_batch",
        "on_hand",
        "updated_by",
        "updated_at",
    )
    list_filter = ("product",)
    search_fields = ("product__name", "batch_label", "source_batch__batch_number")


@admin.register(BundleComposition)
class BundleCompositionAdmin(admin.ModelAdmin):
    list_display = (
        "bundle_product",
        "component_product",
        "qty_per_set",
        "sort_order",
    )
    list_filter = ("bundle_product",)


@admin.register(LoadingSheetLine)
class LoadingSheetLineAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "trip",
        "order",
        "box_no",
        "product",
        "bottles",
        "ready_stock_lot",
        "source_batch",
        "carton_weight_kg",
    )
    list_filter = ("trip",)
    search_fields = (
        "order__po_number",
        "product__name",
        "ready_stock_lot__batch_label",
        "source_batch__batch_number",
    )
