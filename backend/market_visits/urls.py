from django.urls import path

from .views import (
    MarketVisitColumnsView,
    MarketVisitDetailView,
    MarketVisitListCreateView,
)

urlpatterns = [
    path("columns/", MarketVisitColumnsView.as_view(), name="market-visit-columns"),
    path("", MarketVisitListCreateView.as_view(), name="market-visit-list-create"),
    path("<int:pk>/", MarketVisitDetailView.as_view(), name="market-visit-detail"),
]
