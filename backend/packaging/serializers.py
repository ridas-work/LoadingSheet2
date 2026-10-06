from rest_framework import serializers

from .models import PackagingMaterial


class PackagingMaterialSerializer(serializers.ModelSerializer):
    balance = serializers.IntegerField(read_only=True)
    code = serializers.SlugField(required=False, allow_blank=True, max_length=120)

    class Meta:
        model = PackagingMaterial
        fields = [
            "id",
            "name",
            "code",
            "material_type",
            "purchased_qty",
            "rejected_qty",
            "uip_qty",
            "balance",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "uip_qty",
            "balance",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        code = (validated_data.get("code") or "").strip()
        if not code:
            validated_data.pop("code", None)
        return super().create(validated_data)

    def validate(self, attrs):
        purchased = attrs.get(
            "purchased_qty",
            getattr(self.instance, "purchased_qty", 0) if self.instance else 0,
        )
        rejected = attrs.get(
            "rejected_qty",
            getattr(self.instance, "rejected_qty", 0) if self.instance else 0,
        )
        uip = getattr(self.instance, "uip_qty", 0) if self.instance else 0
        if rejected > purchased:
            raise serializers.ValidationError(
                {"rejected_qty": "Rejected/damage cannot exceed purchased quantity."}
            )
        if rejected + uip > purchased:
            raise serializers.ValidationError(
                "Rejected + UIP cannot exceed purchased quantity."
            )
        return attrs
