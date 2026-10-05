from django.contrib import admin

from .models import Customer, OuterBox, Product


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "default_city", "is_approved", "created_at")
    list_filter = ("is_approved",)
    search_fields = ("name", "default_city")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "bottles_per_carton",
        "unit_label",
        "show_on_sheet",
        "is_active",
        "sort_order",
    )
    list_filter = ("is_active", "show_on_sheet", "unit_label")
    search_fields = ("name",)


@admin.register(OuterBox)
class OuterBoxAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
