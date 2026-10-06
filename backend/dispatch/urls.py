from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DispatchPendingOrderListView, TripViewSet

router = DefaultRouter()
router.register("trips", TripViewSet, basename="trip")

urlpatterns = [
    path(
        "dispatch/orders/",
        DispatchPendingOrderListView.as_view(),
        name="dispatch-pending-orders",
    ),
    path("dispatch/", include(router.urls)),
]
