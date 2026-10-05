from rest_framework import generics, status
from rest_framework.response import Response

from accounts.permissions import IsOrderClerkOrAdmin

from .models import Order
from .serializers import OrderCreateSerializer, OrderDetailSerializer, OrderListSerializer


def orders_for_user(user):
    """Clerks only see their own orders; admins see all."""
    qs = Order.objects.select_related("customer", "created_by").prefetch_related(
        "lines__product",
        "custom_cartons__items__product",
        "custom_cartons__outer_box",
    )
    if getattr(user, "role", None) == "admin":
        return qs
    return qs.filter(created_by=user)


class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrderClerkOrAdmin]

    def get_queryset(self):
        return orders_for_user(self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsOrderClerkOrAdmin]
    serializer_class = OrderDetailSerializer

    def get_queryset(self):
        return orders_for_user(self.request.user)
