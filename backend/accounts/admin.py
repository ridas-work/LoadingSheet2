from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "can_market_visit",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "can_market_visit", "is_staff", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Role & access", {"fields": ("role", "can_market_visit")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Role & access", {"fields": ("role", "can_market_visit")}),
    )
