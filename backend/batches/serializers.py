from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from .models import Batch, BatchProduct


class BatchProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchProduct
        fields = ("id", "code", "name", "sort_order")


class BatchSerializer(serializers.ModelSerializer):
    batch_product_id = serializers.PrimaryKeyRelatedField(
        source="batch_product",
        queryset=BatchProduct.objects.filter(is_active=True),
    )
    batch_product_name = serializers.CharField(
        source="batch_product.name", read_only=True
    )
    batch_product_code = serializers.CharField(
        source="batch_product.code", read_only=True
    )
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    created_by_name = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = (
            "id",
            "purpose",
            "batch_number",
            "batch_product_id",
            "batch_product_name",
            "batch_product_code",
            "date",
            "ph",
            "solids",
            "appearance",
            "provider",
            "quantity",
            "quantity_unit",
            "remaining_quantity",
            "customer_name",
            "qc_result",
            "comment",
            "is_closed",
            "is_available",
            "status_label",
            "created_by_username",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "remaining_quantity",
            "is_closed",
            "created_at",
            "updated_at",
        )

    def get_created_by_name(self, obj):
        return obj.created_by.first_name or obj.created_by.username

    def get_is_available(self, obj):
        return obj.is_available

    def get_status_label(self, obj):
        if obj.qc_result == Batch.QCResult.UNSUCCESSFUL:
            return "Unsuccessful"
        if obj.is_closed:
            return "Closed"
        if obj.remaining_quantity <= 0:
            return "Depleted"
        if obj.purpose == Batch.Purpose.SAMPLE:
            rem = obj.remaining_quantity
            if rem == rem.to_integral_value():
                rem_str = str(int(rem))
            else:
                rem_str = format(rem.normalize(), "f")
            return f"Sample ({rem_str} L left)"
        return "Available"

    def validate_batch_number(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Batch number is required.")
        qs = Batch.objects.filter(batch_number__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Batch number already exists.")
        return value

    def validate_quantity(self, value):
        try:
            qty = Decimal(value)
        except (InvalidOperation, TypeError) as exc:
            raise serializers.ValidationError("Invalid quantity.") from exc
        if qty <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return qty

    def create(self, validated_data):
        request = self.context["request"]
        qty = validated_data["quantity"]
        unit = validated_data.get("quantity_unit", Batch.QuantityUnit.L)
        liters = Batch.to_liters(qty, unit)
        return Batch.objects.create(
            created_by=request.user,
            remaining_quantity=liters,
            **validated_data,
        )

    def update(self, instance, validated_data):
        qty = validated_data.get("quantity", instance.quantity)
        unit = validated_data.get("quantity_unit", instance.quantity_unit)
        old_liters = Batch.to_liters(instance.quantity, instance.quantity_unit)
        new_liters = Batch.to_liters(qty, unit)
        # Adjust remaining by the change in original volume
        delta = new_liters - old_liters
        remaining = instance.remaining_quantity + delta
        if remaining < 0:
            remaining = Decimal("0")

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.remaining_quantity = remaining
        instance.save()
        return instance
