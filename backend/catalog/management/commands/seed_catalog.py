from django.core.management.base import BaseCommand

from catalog.models import Customer, OuterBox, Product


# (name, units_per_carton, unit_label, sort_order)
SHEET_PRODUCTS = [
    ("Brighten Laundry Detergent (pouch)(1 litre)", 20, "bottles", 1),
    ("Brighten Liquid Laundry Detergent (1 litre)", 10, "bottles", 2),
    ("Brighten bottle B2G1", 5, "bundles", 3),
    ("Brighten pouch B2G1", 10, "bundles", 4),
    ("Fabrito Fabric Softener (1 litre)", 10, "bottles", 5),
    ("Fabrito Fabric Softener (pouch)(1 litre)", 20, "bottles", 6),
    ("Fabrito bottle B2G1", 5, "bundles", 7),
    ("Fabrito Pouch B2G1", 10, "bundles", 8),
    ("Degrease Spray 750ml", 10, "bottles", 9),
    ("Degrease 750 ml B2G1", 5, "bundles", 10),
    ("Glim 750ml", 10, "bottles", 11),
    ("Power Wash 500ml", 10, "bottles", 12),
    ("Power Wash 1 Litre (pouch)", 20, "bottles", 13),
    ("Power Wash 500ml B2G1", 5, "bundles", 14),
    ("Power wash Pouch B2G1", 10, "bundles", 15),
    ("Rhino 250ml", 20, "bottles", 16),
    ("Rhino 500ml", 30, "bottles", 17),
    ("Rhino 750ml", 10, "bottles", 18),
    ("Titan 500 g", 10, "bottles", 19),
    ("Titan 1.25 kg", 8, "bottles", 20),
    ("Washout Multi-surface Disinfectant Floral Red", 10, "bottles", 21),
    ("Washout Multi-surface Disinfectant Lemon Yellow", 10, "bottles", 22),
    ("Washout Multi-surface Disinfectant Ocean Blue", 10, "bottles", 23),
    ("Washout B2G1 (Floral + Ocean + Lemon)", 5, "bundles", 24),
    (
        "Brighten Laundry Detergent + Fabrito Fabric Softener bundle (1 litre each)",
        5,
        "bundles",
        25,
    ),
    ("Power Wash Dish Wash + Degrease Spray Bundle", 5, "bundles", 26),
    ("Rhino 2x2 750ml", 5, "bundles", 27),
    ("Rhino 250 ml B2G1", 10, "bundles", 28),
    ("Rhino 500 ml B2G1", 15, "bundles", 29),
    ("Rhino 750 ml B2G1", 5, "bundles", 30),
]


class Command(BaseCommand):
    help = "Seed catalog: approved customers, sheet products, outer boxes"

    def handle(self, *args, **options):
        customers = [
            ("Demo Traders", "LAHORE"),
            ("City Mart", "KARACHI"),
            ("Green Supplies", "ISLAMABAD"),
        ]
        for name, city in customers:
            Customer.objects.get_or_create(
                name=name,
                defaults={"default_city": city, "is_approved": True},
            )

        sheet_names = set()
        for name, units, unit_label, order in SHEET_PRODUCTS:
            sheet_names.add(name)
            Product.objects.update_or_create(
                name=name,
                defaults={
                    "bottles_per_carton": units,
                    "unit_label": unit_label,
                    "show_on_sheet": True,
                    "is_active": True,
                    "sort_order": order,
                },
            )

        # Hide any products not on the official sheet list
        deactivated = (
            Product.objects.exclude(name__in=sheet_names)
            .filter(is_active=True)
            .update(is_active=False, show_on_sheet=False)
        )

        for box_name in (
            "Generic Custom Box",
            "Standard Product Box",
            "Large Outer Carton",
        ):
            OuterBox.objects.get_or_create(name=box_name, defaults={"is_active": True})

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalog seeded: {len(sheet_names)} sheet products "
                f"({deactivated} other products deactivated)."
            )
        )
