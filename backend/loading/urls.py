from django.urls import path

from .ready_stock_views import (
    ReadyStockBatchesView,
    ReadyStockDetailView,
    ReadyStockFormMetaView,
    ReadyStockListCreateView,
    ReadyStockOptionsView,
)
from .views import (
    LoadingSheetView,
    LoadingTripDeliverView,
    LoadingTripDetailView,
    LoadingTripListView,
    PendingOrderListView,
)

urlpatterns = [
    path(
        "loading/pending-orders/",
        PendingOrderListView.as_view(),
        name="loading-pending-orders",
    ),
    path(
        "loading/ready-stock/",
        ReadyStockListCreateView.as_view(),
        name="loading-ready-stock",
    ),
    path(
        "loading/ready-stock/form-meta/",
        ReadyStockFormMetaView.as_view(),
        name="loading-ready-stock-meta",
    ),
    path(
        "loading/ready-stock/options/",
        ReadyStockOptionsView.as_view(),
        name="loading-ready-stock-options",
    ),
    path(
        "loading/ready-stock/batches/",
        ReadyStockBatchesView.as_view(),
        name="loading-ready-stock-batches",
    ),
    path(
        "loading/ready-stock/<int:pk>/",
        ReadyStockDetailView.as_view(),
        name="loading-ready-stock-detail",
    ),
    path("loading/trips/", LoadingTripListView.as_view(), name="loading-trips"),
    path(
        "loading/trips/<int:pk>/",
        LoadingTripDetailView.as_view(),
        name="loading-trip-detail",
    ),
    path(
        "loading/trips/<int:trip_id>/sheet/",
        LoadingSheetView.as_view(),
        name="loading-trip-sheet",
    ),
    path(
        "loading/trips/<int:trip_id>/deliver/",
        LoadingTripDeliverView.as_view(),
        name="loading-trip-deliver",
    ),
]
