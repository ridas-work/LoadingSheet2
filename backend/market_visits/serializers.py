from django.db import transaction
from rest_framework import serializers

from .columns import COLUMN_CODES, empty_availability, empty_facing
from .models import MarketVisit, MarketVisitStore


class MarketVisitStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketVisitStore
        fields = (
            "id",
            "store_name",
            "location",
            "remarks",
            "availability",
            "facing",
            "sort_order",
        )


class MarketVisitListSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    store_count = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    first_location = serializers.SerializerMethodField()

    class Meta:
        model = MarketVisit
        fields = (
            "id",
            "visit_date",
            "status",
            "created_by_username",
            "store_count",
            "title",
            "first_location",
            "created_at",
            "updated_at",
        )

    def _stores(self, obj):
        if (
            hasattr(obj, "_prefetched_objects_cache")
            and "stores" in obj._prefetched_objects_cache
        ):
            return list(obj.stores.all())
        return list(obj.stores.all())

    def get_store_count(self, obj):
        return len(self._stores(obj))

    def get_title(self, obj):
        stores = self._stores(obj)
        count = len(stores)
        if count == 0:
            return f"Market visit {obj.visit_date}"
        if count == 1:
            return stores[0].store_name
        return f"{count} stores"

    def get_first_location(self, obj):
        stores = self._stores(obj)
        if not stores:
            return ""
        return stores[0].location or ""


class MarketVisitSerializer(serializers.ModelSerializer):
    stores = MarketVisitStoreSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    store_count = serializers.SerializerMethodField()

    class Meta:
        model = MarketVisit
        fields = (
            "id",
            "visit_date",
            "status",
            "created_by_username",
            "store_count",
            "stores",
            "created_at",
            "updated_at",
        )

    def get_store_count(self, obj):
        if (
            hasattr(obj, "_prefetched_objects_cache")
            and "stores" in obj._prefetched_objects_cache
        ):
            return len(obj.stores.all())
        return obj.stores.count()


class MarketVisitStoreWriteSerializer(serializers.Serializer):
    store_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    location = serializers.CharField(required=False, allow_blank=True, max_length=255)
    remarks = serializers.CharField(required=False, allow_blank=True)
    availability = serializers.DictField(
        required=False, child=serializers.CharField(allow_blank=True)
    )
    facing = serializers.DictField(required=False)


class MarketVisitWriteSerializer(serializers.Serializer):
    visit_date = serializers.DateField()
    action = serializers.ChoiceField(choices=("save", "submit"))
    stores = MarketVisitStoreWriteSerializer(many=True)

    def validate_stores(self, stores):
        cleaned = []
        for index, store in enumerate(stores):
            name = (store.get("store_name") or "").strip()
            location = (store.get("location") or "").strip()
            remarks = (store.get("remarks") or "").strip()
            availability = store.get("availability") or {}
            facing = store.get("facing") or {}

            if not name:
                has_data = bool(location or remarks)
                has_data = has_data or any(
                    str(availability.get(code, "")).strip() for code in COLUMN_CODES
                )
                has_data = has_data or any(
                    (
                        facing.get(code) not in (None, "", "0")
                        for code in COLUMN_CODES
                        if code in facing
                    )
                ) or any(
                    isinstance(facing.get(code), int) and facing.get(code) > 0
                    for code in COLUMN_CODES
                )
                if has_data:
                    raise serializers.ValidationError(
                        {index: "Store name is required when other fields are filled."}
                    )
                continue

            avail_out = empty_availability()
            for code in COLUMN_CODES:
                raw = str(availability.get(code, "") or "").strip().upper()
                if raw in ("", "—", "-"):
                    avail_out[code] = ""
                elif raw in ("Y", "N"):
                    avail_out[code] = raw
                else:
                    raise serializers.ValidationError(
                        {index: f"Availability for {code} must be blank, Y, or N."}
                    )

            facing_out = empty_facing()
            for code in COLUMN_CODES:
                raw = facing.get(code, None)
                if raw in (None, "", "—", "-"):
                    facing_out[code] = None
                    continue
                try:
                    qty = int(raw)
                except (TypeError, ValueError) as exc:
                    raise serializers.ValidationError(
                        {index: f"Facing for {code} must be a whole number."}
                    ) from exc
                if qty < 0:
                    raise serializers.ValidationError(
                        {index: f"Facing for {code} cannot be negative."}
                    )
                facing_out[code] = qty

            cleaned.append(
                {
                    "store_name": name,
                    "location": location,
                    "remarks": remarks,
                    "availability": avail_out,
                    "facing": facing_out,
                }
            )
        return cleaned

    def _target_status(self):
        if self.validated_data["action"] == "submit":
            return MarketVisit.Status.SUBMITTED
        return MarketVisit.Status.IN_PROCESS

    def _replace_stores(self, visit, stores):
        visit.stores.all().delete()
        MarketVisitStore.objects.bulk_create(
            [
                MarketVisitStore(
                    visit=visit,
                    store_name=row["store_name"],
                    location=row["location"],
                    remarks=row["remarks"],
                    availability=row["availability"],
                    facing=row["facing"],
                    sort_order=index,
                )
                for index, row in enumerate(stores)
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        visit = MarketVisit.objects.create(
            created_by=self.context["request"].user,
            visit_date=validated_data["visit_date"],
            status=self._target_status(),
        )
        self._replace_stores(visit, validated_data["stores"])
        return (
            MarketVisit.objects.prefetch_related("stores")
            .select_related("created_by")
            .get(pk=visit.pk)
        )

    @transaction.atomic
    def update(self, visit, validated_data):
        visit.visit_date = validated_data["visit_date"]
        visit.status = self._target_status()
        visit.save(update_fields=["visit_date", "status", "updated_at"])
        self._replace_stores(visit, validated_data["stores"])
        return (
            MarketVisit.objects.prefetch_related("stores")
            .select_related("created_by")
            .get(pk=visit.pk)
        )
