from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from catalog.models import WEIGHT_TOLERANCE_PCT
from dispatch.models import Trip
from orders.models import Order

from .models import BundleComposition, LoadingSheetLine, ReadyStockLot
from .services import progress_for_queryset


class PendingOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    total_products = serializers.IntegerField(read_only=True)
    total_bottles = serializers.IntegerField(read_only=True)
    trip_id = serializers.SerializerMethodField()
    trip_vehicle_no = serializers.SerializerMethodField()
    trip_status = serializers.SerializerMethodField()
    challan_no = serializers.SerializerMethodField()
    on_trip = serializers.SerializerMethodField()

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
            "on_trip",
            "trip_id",
            "trip_vehicle_no",
            "trip_status",
            "challan_no",
            "created_at",
        )

    def _assignment(self, obj):
        try:
            return obj.trip_assignment
        except ObjectDoesNotExist:
            return None

    def get_on_trip(self, obj):
        return self._assignment(obj) is not None

    def get_trip_id(self, obj):
        a = self._assignment(obj)
        return a.trip_id if a else None

    def get_trip_vehicle_no(self, obj):
        a = self._assignment(obj)
        return a.trip.vehicle_no if a else ""

    def get_trip_status(self, obj):
        a = self._assignment(obj)
        return a.trip.status if a else None

    def get_challan_no(self, obj):
        a = self._assignment(obj)
        return a.challan_no if a else ""


class ReadyStockLotSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    source_batch_id = serializers.IntegerField(read_only=True, allow_null=True)
    is_bundle = serializers.SerializerMethodField()
    unit_label = serializers.SerializerMethodField()
    assigned_bottles = serializers.SerializerMethodField()
    available_to_assign = serializers.SerializerMethodField()

    class Meta:
        model = ReadyStockLot
        fields = (
            "id",
            "product_id",
            "product_name",
            "batch_label",
            "source_batch_id",
            "on_hand",
            "assigned_bottles",
            "available_to_assign",
            "is_bundle",
            "unit_label",
            "updated_at",
        )

    def _bundle_ids(self):
        if "bundle_product_ids" not in self.context:
            self.context["bundle_product_ids"] = set(
                BundleComposition.objects.values_list(
                    "bundle_product_id", flat=True
                ).distinct()
            )
        return self.context["bundle_product_ids"]

    def _reserved_map(self):
        if "reserved_by_lot" not in self.context:
            from .services import reserved_bottles_by_lot

            exclude = self.context.get("exclude_trip_id")
            self.context["reserved_by_lot"] = reserved_bottles_by_lot(
                exclude_trip_id=exclude
            )
        return self.context["reserved_by_lot"]

    def get_is_bundle(self, obj):
        return obj.product_id in self._bundle_ids()

    def get_unit_label(self, obj):
        return "sets" if self.get_is_bundle(obj) else "bottles"

    def get_assigned_bottles(self, obj):
        return self._reserved_map().get(obj.id, 0)

    def get_available_to_assign(self, obj):
        from .services import available_to_assign

        return available_to_assign(obj.on_hand, self.get_assigned_bottles(obj))


class ReadyStockComponentInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    batch_id = serializers.IntegerField(required=False, allow_null=True)
    batch_label = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )


class ReadyStockAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    batch_id = serializers.IntegerField(required=False, allow_null=True)
    batch_label = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )
    bottles = serializers.IntegerField(required=False, min_value=1)
    sets = serializers.IntegerField(required=False, min_value=1)
    components = ReadyStockComponentInputSerializer(many=True, required=False)


class ReadyStockPatchSerializer(serializers.Serializer):
    on_hand = serializers.IntegerField(required=False, min_value=0)
    batch_label = serializers.CharField(required=False, max_length=64)


class LoadingTripOrderSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    po_number = serializers.CharField()
    customer_name = serializers.CharField()
    city = serializers.CharField()
    challan_no = serializers.CharField()
    assigned_lines = serializers.IntegerField()
    total_lines = serializers.IntegerField()


class LoadingTripListSerializer(serializers.ModelSerializer):
    po_numbers = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    assigned_lines = serializers.SerializerMethodField()
    total_lines = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            "id",
            "vehicle_no",
            "driver_name",
            "default_challan_no",
            "status",
            "po_numbers",
            "order_count",
            "assigned_lines",
            "total_lines",
            "created_by_name",
            "updated_at",
            "created_at",
        )

    def get_po_numbers(self, obj):
        return [to.order.po_number for to in obj.trip_orders.all()]

    def get_order_count(self, obj):
        return obj.trip_orders.count()

    def get_assigned_lines(self, obj):
        assigned, _ = progress_for_queryset(obj.sheet_lines.all())
        return assigned

    def get_total_lines(self, obj):
        _, total = progress_for_queryset(obj.sheet_lines.all())
        return total

    def get_created_by_name(self, obj):
        return obj.created_by.first_name or obj.created_by.username


class LoadingTripDetailSerializer(LoadingTripListSerializer):
    trip_orders = serializers.SerializerMethodField()
    helper_name = serializers.CharField()
    production_incharge = serializers.CharField()
    security = serializers.CharField()

    class Meta(LoadingTripListSerializer.Meta):
        fields = LoadingTripListSerializer.Meta.fields + (
            "helper_name",
            "production_incharge",
            "security",
            "trip_orders",
        )

    def get_trip_orders(self, obj):
        rows = []
        for to in obj.trip_orders.select_related("order", "order__customer").all():
            qs = obj.sheet_lines.filter(order=to.order)
            assigned, total = progress_for_queryset(qs)
            rows.append(
                {
                    "order_id": to.order_id,
                    "po_number": to.order.po_number,
                    "customer_name": to.order.customer.name,
                    "city": to.order.city,
                    "challan_no": to.challan_no,
                    "assigned_lines": assigned,
                    "total_lines": total,
                }
            )
        return rows


class LoadingSheetLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    bottles_per_carton = serializers.IntegerField(
        source="product.bottles_per_carton", read_only=True
    )
    standard_weight_kg = serializers.DecimalField(
        source="product.standard_carton_weight_kg",
        max_digits=8,
        decimal_places=3,
        read_only=True,
        allow_null=True,
    )
    weight_tolerance_pct = serializers.SerializerMethodField()
    ready_stock_lot_id = serializers.IntegerField(read_only=True, allow_null=True)
    source_batch_id = serializers.IntegerField(read_only=True, allow_null=True)
    batch_label = serializers.SerializerMethodField()
    lot_on_hand = serializers.SerializerMethodField()
    batch_remaining_liters = serializers.SerializerMethodField()
    po_number = serializers.CharField(source="order.po_number", read_only=True)
    challan_no = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source="order.customer.name", read_only=True)

    class Meta:
        model = LoadingSheetLine
        fields = (
            "id",
            "order_id",
            "box_no",
            "product_id",
            "product_name",
            "bottles",
            "bottles_per_carton",
            "standard_weight_kg",
            "weight_tolerance_pct",
            "ready_stock_lot_id",
            "source_batch_id",
            "batch_label",
            "lot_on_hand",
            "batch_remaining_liters",
            "carton_weight_kg",
            "po_number",
            "customer_name",
            "challan_no",
            "sort_order",
        )

    def get_weight_tolerance_pct(self, obj):
        return WEIGHT_TOLERANCE_PCT

    def get_batch_label(self, obj):
        if obj.ready_stock_lot_id:
            return obj.ready_stock_lot.batch_label
        if obj.source_batch_id:
            return obj.source_batch.batch_number
        return None

    def get_lot_on_hand(self, obj):
        return obj.ready_stock_lot.on_hand if obj.ready_stock_lot_id else None

    def get_batch_remaining_liters(self, obj):
        if obj.source_batch_id:
            return str(obj.source_batch.remaining_quantity)
        return None

    def get_challan_no(self, obj):
        challans = self.context.get("challan_by_order") or {}
        return challans.get(obj.order_id, "")


class SheetSaveLineSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ready_stock_lot_id = serializers.IntegerField(required=False, allow_null=True)
    source_batch_id = serializers.IntegerField(required=False, allow_null=True)
    carton_weight_kg = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        required=False,
        allow_null=True,
    )


class SheetSaveSerializer(serializers.Serializer):
    lines = SheetSaveLineSerializer(many=True)
