from django.core.management.base import BaseCommand

from catalog.models import Customer, OuterBox, Product


# (name, units_per_carton, unit_label, sort_order)
SHEET_PRODUCTS = [
    ("Brighten Laundry Detergent (pouch)(1 litre)", 20, "bottles", 1),
    ("Brighten Liquid Laundry Detergent (1 litre)", 10, "bottles", 2),
    ("Brighten bottle B2G1", 5, "bundles", 3),
    ("Fabrito Fabric Softener (1 litre)", 10, "bottles", 4),
    ("Fabrito Fabric Softener (pouch)(1 litre)", 20, "bottles", 5),
    ("Fabrito bottle B2G1", 5, "bundles", 6),
    ("Degrease Spray 750ml", 10, "bottles", 7),
    ("Degrease 750 ml B2G1", 5, "bundles", 8),
    ("Glim 750ml", 10, "bottles", 9),
    ("Power Wash 500ml", 10, "bottles", 10),
    ("Power Wash 1 Litre (pouch)", 20, "bottles", 11),
    ("Power Wash 500ml B2G1", 5, "bundles", 12),
    ("Rhino 250ml", 20, "bottles", 13),
    ("Rhino 500ml", 30, "bottles", 14),
    ("Rhino 750ml", 10, "bottles", 15),
    ("Titan 500 g", 10, "bottles", 16),
    ("Titan 1.25 kg", 8, "bottles", 17),
    ("Washout Multi-surface Disinfectant Floral Red", 10, "bottles", 18),
    ("Washout Multi-surface Disinfectant Lemon Yellow", 10, "bottles", 19),
    ("Washout Multi-surface Disinfectant Ocean Blue", 10, "bottles", 20),
    ("Washout B2G1 (Floral + Ocean + Lemon)", 5, "bundles", 21),
    (
        "Brighten Laundry Detergent + Fabrito Fabric Softener bundle (1 litre each)",
        5,
        "bundles",
        22,
    ),
    ("Power Wash Dish Wash + Degrease Spray Bundle", 5, "bundles", 23),
    ("Rhino 2x2 750ml", 5, "bundles", 24),
    ("Rhino 250 ml B2G1", 10, "bundles", 25),
    ("Rhino 500 ml B2G1", 15, "bundles", 26),
    ("Rhino 750 ml B2G1", 5, "bundles", 27),
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

        # Only sheet products stay active; former custom-carton names are deactivated
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
