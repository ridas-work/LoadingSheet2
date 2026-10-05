from django.contrib import admin

from .models import CustomCarton, CustomCartonItem, Order, OrderLine


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0


class CustomCartonItemInline(admin.TabularInline):
    model = CustomCartonItem
    extra = 0


class CustomCartonInline(admin.StackedInline):
    model = CustomCarton
    extra = 0
    show_change_link = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "po_number",
        "customer",
        "city",
        "deadline_date",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "city")
    search_fields = ("po_number", "customer__name")
    inlines = [OrderLineInline, CustomCartonInline]


@admin.register(CustomCarton)
class CustomCartonAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "identical_count", "label", "outer_box")
    inlines = [CustomCartonItemInline]
