from django.contrib import admin

from .models import MarketVisit, MarketVisitStore


class MarketVisitStoreInline(admin.TabularInline):
    model = MarketVisitStore
    extra = 0


@admin.register(MarketVisit)
class MarketVisitAdmin(admin.ModelAdmin):
    list_display = ("visit_date", "created_by", "status", "updated_at")
    list_filter = ("status", "visit_date")
    inlines = [MarketVisitStoreInline]
