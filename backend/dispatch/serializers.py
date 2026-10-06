from django.db import transaction
from rest_framework import serializers

from orders.models import Order

from .models import Trip, TripOrder


class DispatchOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    total_products = serializers.IntegerField(read_only=True)
    total_bottles = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "po_number",
            "customer_name",
            "city",
            "deadline_date",
            "status",
            "created_by_username",
            "total_products",
            "total_bottles",
            "created_at",
        )


class TripOrderItemSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    challan_no = serializers.CharField(
        required=False, allow_blank=True, max_length=128, default=""
    )


class TripOrderReadSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    po_number = serializers.CharField(source="order.po_number", read_only=True)
    customer_name = serializers.CharField(
        source="order.customer.name", read_only=True
    )
    city = serializers.CharField(source="order.city", read_only=True)
    deadline_date = serializers.DateField(
        source="order.deadline_date", read_only=True
    )
    created_by_username = serializers.CharField(
        source="order.created_by.username", read_only=True
    )

    class Meta:
        model = TripOrder
        fields = (
            "id",
            "order_id",
            "po_number",
            "customer_name",
            "city",
            "deadline_date",
            "created_by_username",
            "challan_no",
            "sort_order",
        )


class TripSerializer(serializers.ModelSerializer):
    orders = TripOrderItemSerializer(many=True, write_only=True)
    trip_orders = TripOrderReadSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    created_by_name = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            "id",
            "vehicle_no",
            "driver_name",
            "helper_name",
            "production_incharge",
            "security",
            "default_challan_no",
            "status",
            "orders",
            "trip_orders",
            "order_count",
            "created_by_username",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "created_at", "updated_at")

    def get_created_by_name(self, obj):
        return obj.created_by.first_name or obj.created_by.username

    def get_order_count(self, obj):
        if hasattr(obj, "annotated_order_count"):
            return obj.annotated_order_count
        return obj.trip_orders.count()

    def validate_orders(self, value):
        if not value:
            raise serializers.ValidationError(
                "Select at least one order for this trip."
            )
        order_ids = [item["order_id"] for item in value]
        if len(order_ids) != len(set(order_ids)):
            raise serializers.ValidationError("Duplicate orders in trip.")
        return value

    def _resolve_orders(self, items, trip=None):
        order_ids = [item["order_id"] for item in items]
        orders = {
            o.id: o
            for o in Order.objects.filter(
                id__in=order_ids, status=Order.Status.SUBMITTED
            ).select_related("customer", "created_by")
        }
        missing = set(order_ids) - set(orders.keys())
        if missing:
            raise serializers.ValidationError(
                {"orders": f"Unknown or invalid order ids: {sorted(missing)}"}
            )

        assigned = TripOrder.objects.filter(order_id__in=order_ids)
        if trip is not None:
            assigned = assigned.exclude(trip=trip)
        conflicts = list(assigned.values_list("order_id", flat=True))
        if conflicts:
            raise serializers.ValidationError(
                {
                    "orders": (
                        "These orders are already on another trip: "
                        f"{sorted(conflicts)}"
                    )
                }
            )
        return orders

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("orders")
        orders = self._resolve_orders(items)
        trip = Trip.objects.create(
            **validated_data,
            created_by=self.context["request"].user,
            status=Trip.Status.PLANNED,
        )
        for idx, item in enumerate(items):
            TripOrder.objects.create(
                trip=trip,
                order=orders[item["order_id"]],
                challan_no=item.get("challan_no") or "",
                sort_order=idx,
            )
        return trip

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.status == Trip.Status.DELIVERED:
            raise serializers.ValidationError(
                "Delivered trips cannot be edited."
            )
        items = validated_data.pop("orders", None)
        for field in (
            "vehicle_no",
            "driver_name",
            "helper_name",
            "production_incharge",
            "security",
            "default_challan_no",
        ):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        if items is not None:
            orders = self._resolve_orders(items, trip=instance)
            instance.trip_orders.all().delete()
            for idx, item in enumerate(items):
                TripOrder.objects.create(
                    trip=instance,
                    order=orders[item["order_id"]],
                    challan_no=item.get("challan_no") or "",
                    sort_order=idx,
                )
        return instance
