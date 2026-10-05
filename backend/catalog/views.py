from rest_framework import generics

from accounts.permissions import IsOrderClerkOrAdmin

from .models import Customer, OuterBox, Product
from .serializers import CustomerSerializer, OuterBoxSerializer, ProductSerializer


class CustomerListView(generics.ListAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsOrderClerkOrAdmin]

    def get_queryset(self):
        return Customer.objects.filter(is_approved=True)


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsOrderClerkOrAdmin]

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True)
        scope = self.request.query_params.get("for")
        if scope == "sheet":
            return qs.filter(show_on_sheet=True)
        if scope == "custom":
            return qs.filter(show_on_sheet=False)
        return qs


class OuterBoxListView(generics.ListAPIView):
    serializer_class = OuterBoxSerializer
    permission_classes = [IsOrderClerkOrAdmin]

    def get_queryset(self):
        return OuterBox.objects.filter(is_active=True)
