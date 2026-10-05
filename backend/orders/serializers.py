from django.db import transaction
from rest_framework import serializers

from catalog.models import Customer, OuterBox, Product

from .models import ContainerSize, CustomCarton, CustomCartonItem, Order, OrderLine


class CustomCartonItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    container_size = serializers.ChoiceField(choices=ContainerSize.choices)
    qty = serializers.IntegerField(min_value=1)


class CustomCartonWriteSerializer(serializers.Serializer):
    identical_count = serializers.IntegerField(min_value=1, default=1)
    label = serializers.CharField(required=False, allow_blank=True, max_length=255)
    outer_box_id = serializers.IntegerField()
    items = CustomCartonItemWriteSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "Each custom carton needs at least one product line."
            )
        return value


class OrderLineWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    bottles = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    po_number = serializers.CharField(max_length=128)
    customer_id = serializers.IntegerField()
    city = serializers.CharField(max_length=128)
    deadline_date = serializers.DateField()
    lines = OrderLineWriteSerializer(many=True, required=False, default=list)
    custom_cartons = CustomCartonWriteSerializer(many=True, required=False, default=list)

    def validate_customer_id(self, value):
        try:
            customer = Customer.objects.get(pk=value, is_approved=True)
        except Customer.DoesNotExist as exc:
            raise serializers.ValidationError(
                "Customer not found or not approved."
            ) from exc
        self.context["customer"] = customer
        return value

    def validate(self, attrs):
        lines = attrs.get("lines") or []
        custom_cartons = attrs.get("custom_cartons") or []
        if not lines and not custom_cartons:
            raise serializers.ValidationError(
                "Add at least one product line or custom carton."
            )

        product_ids = {line["product_id"] for line in lines}
        for carton in custom_cartons:
            for item in carton["items"]:
                product_ids.add(item["product_id"])

        products = {
            p.id: p for p in Product.objects.filter(id__in=product_ids, is_active=True)
        }
        missing = product_ids - set(products.keys())
        if missing:
            raise serializers.ValidationError(
                {"products": f"Unknown or inactive product ids: {sorted(missing)}"}
            )

        outer_ids = {c["outer_box_id"] for c in custom_cartons}
        outer_boxes = {
            o.id: o for o in OuterBox.objects.filter(id__in=outer_ids, is_active=True)
        }
        missing_outer = outer_ids - set(outer_boxes.keys())
        if missing_outer:
            raise serializers.ValidationError(
                {
                    "outer_boxes": f"Unknown or inactive outer box ids: {sorted(missing_outer)}"
                }
            )

        # de-dupe product lines by product_id (last wins)
        deduped = {}
        for line in lines:
            deduped[line["product_id"]] = line
        attrs["lines"] = list(deduped.values())

        line_errors = []
        for line in attrs["lines"]:
            product = products[line["product_id"]]
            qty = line["bottles"]
            per_carton = product.bottles_per_carton
            if qty % per_carton != 0:
                unit = product.unit_label
                line_errors.append(
                    f"{product.name}: qty must be a multiple of {per_carton} "
                    f"{unit}/carton (e.g. {per_carton}, {per_carton * 2}, "
                    f"{per_carton * 3}…). Got {qty}."
                )
        if line_errors:
            raise serializers.ValidationError({"lines": line_errors})

        attrs["_products"] = products
        attrs["_outer_boxes"] = outer_boxes
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        customer = self.context["customer"]
        products = validated_data.pop("_products")
        outer_boxes = validated_data.pop("_outer_boxes")
        lines_data = validated_data.pop("lines", [])
        cartons_data = validated_data.pop("custom_cartons", [])

        order = Order.objects.create(
            po_number=validated_data["po_number"].strip(),
            customer=customer,
            city=validated_data["city"].strip(),
            deadline_date=validated_data["deadline_date"],
            created_by=request.user,
        )

        OrderLine.objects.bulk_create(
            [
                OrderLine(
                    order=order,
                    product=products[line["product_id"]],
                    bottles=line["bottles"],
                )
                for line in lines_data
            ]
        )

        for carton_data in cartons_data:
            carton = CustomCarton.objects.create(
                order=order,
                identical_count=carton_data["identical_count"],
                label=(carton_data.get("label") or "").strip(),
                outer_box=outer_boxes[carton_data["outer_box_id"]],
            )
            CustomCartonItem.objects.bulk_create(
                [
                    CustomCartonItem(
                        custom_carton=carton,
                        product=products[item["product_id"]],
                        container_size=item["container_size"],
                        qty=item["qty"],
                    )
                    for item in carton_data["items"]
                ]
            )

        return order


class CustomCartonItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="product.id")
    product_name = serializers.CharField(source="product.name")

    class Meta:
        model = CustomCartonItem
        fields = ("id", "product_id", "product_name", "container_size", "qty")


class CustomCartonSerializer(serializers.ModelSerializer):
    outer_box_id = serializers.IntegerField(source="outer_box.id")
    outer_box_name = serializers.CharField(source="outer_box.name")
    items = CustomCartonItemSerializer(many=True, read_only=True)

    class Meta:
        model = CustomCarton
        fields = (
            "id",
            "identical_count",
            "label",
            "outer_box_id",
            "outer_box_name",
            "items",
        )


class OrderLineSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="product.id")
    product_name = serializers.CharField(source="product.name")
    bottles_per_carton = serializers.IntegerField(source="product.bottles_per_carton")
    cartons = serializers.SerializerMethodField()

    class Meta:
        model = OrderLine
        fields = (
            "id",
            "product_id",
            "product_name",
            "bottles",
            "bottles_per_carton",
            "cartons",
        )

    def get_cartons(self, obj):
        return obj.cartons


class OrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name")
    created_by_username = serializers.CharField(source="created_by.username")
    total_bottles = serializers.SerializerMethodField()
    total_products = serializers.SerializerMethodField()

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
            "created_at",
            "total_bottles",
            "total_products",
        )

    def get_total_bottles(self, obj):
        return sum(line.bottles for line in obj.lines.all())

    def get_total_products(self, obj):
        return obj.lines.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source="customer.id")
    customer_name = serializers.CharField(source="customer.name")
    created_by_username = serializers.CharField(source="created_by.username")
    lines = OrderLineSerializer(many=True, read_only=True)
    custom_cartons = CustomCartonSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "po_number",
            "customer_id",
            "customer_name",
            "city",
            "deadline_date",
            "status",
            "created_by_username",
            "created_at",
            "updated_at",
            "lines",
            "custom_cartons",
        )
