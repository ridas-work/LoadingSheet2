from rest_framework import serializers

from .models import Customer, OuterBox, Product


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "name", "default_city", "is_approved")


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "bottles_per_carton",
            "unit_label",
            "show_on_sheet",
            "is_active",
            "sort_order",
        )


class OuterBoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = OuterBox
        fields = ("id", "name", "is_active")
