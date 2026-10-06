from django.contrib import admin

from .models import Trip, TripOrder


class TripOrderInline(admin.TabularInline):
    model = TripOrder
    extra = 0


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vehicle_no",
        "driver_name",
        "default_challan_no",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("vehicle_no", "driver_name", "default_challan_no")
    inlines = [TripOrderInline]


@admin.register(TripOrder)
class TripOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "trip", "order", "challan_no", "sort_order")
    search_fields = ("order__po_number", "challan_no")
