from django.db.models import Count, Prefetch, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError

from accounts.permissions import IsDispatchClerkOrAdmin
from orders.models import Order

from .models import Trip, TripOrder
from .serializers import DispatchOrderSerializer, TripSerializer


class DispatchPendingOrderListView(generics.ListAPIView):
    """All clerks' submitted orders not already assigned to a trip."""

    serializer_class = DispatchOrderSerializer
    permission_classes = [IsDispatchClerkOrAdmin]

    def get_queryset(self):
        assigned_ids = TripOrder.objects.values_list("order_id", flat=True)
        return (
            Order.objects.filter(status=Order.Status.SUBMITTED)
            .exclude(id__in=assigned_ids)
            .select_related("customer", "created_by")
            .annotate(
                total_products=Count("lines", distinct=True),
                total_bottles=Coalesce(Sum("lines__bottles"), Value(0)),
            )
            .order_by("-created_at")
        )


class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    permission_classes = [IsDispatchClerkOrAdmin]
    http_method_names = ["get", "post", "put", "head", "options"]

    def get_queryset(self):
        return (
            Trip.objects.select_related("created_by")
            .prefetch_related(
                Prefetch(
                    "trip_orders",
                    queryset=TripOrder.objects.select_related(
                        "order", "order__customer", "order__created_by"
                    ),
                )
            )
            .annotate(annotated_order_count=Count("trip_orders", distinct=True))
        )

    def perform_update(self, serializer):
        if serializer.instance.status == Trip.Status.DELIVERED:
            raise ValidationError("Delivered trips cannot be edited.")
        serializer.save()
