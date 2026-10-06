from decimal import Decimal
from typing import Optional

from django.core.management.base import BaseCommand

from batches.models import BatchProduct
from catalog.models import Customer, OuterBox, Product


def batch_product_code_for(name: str) -> Optional[str]:
    n = name.lower()
    if n.startswith("rhino"):
        return "rhino"
    if n.startswith("brighten"):
        return "brighten"
    if n.startswith("fabrito"):
        return "fabrito"
    if n.startswith("degrease"):
        return "degrease"
    if n.startswith("glim"):
        return "glim"
    if n.startswith("power wash"):
        return "power_wash"
    if n.startswith("titan"):
        return "titan"
    if n.startswith("washout"):
        if "floral" in n and "ocean" not in n and "lemon" not in n:
            return "washout_floral"
        if "lemon" in n and "floral" not in n and "ocean" not in n:
            return "washout_lemon"
        if "ocean" in n and "floral" not in n and "lemon" not in n:
            return "washout_ocean"
        # multi-scent B2G1 — no single parent
        return None
    return None


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

# Standard full-carton weight (kg) used for Rashid's ±8% check.
STANDARD_CARTON_WEIGHT_KG = {
    "Brighten Laundry Detergent (pouch)(1 litre)": "21.42",
    "Brighten Liquid Laundry Detergent (1 litre)": "11.7",
    "Brighten bottle B2G1": "15.567",
    "Fabrito Fabric Softener (1 litre)": "11.05",
    "Fabrito Fabric Softener (pouch)(1 litre)": "21.43",
    "Fabrito bottle B2G1": "15.567",
    "Degrease Spray 750ml": "8.75",
    "Degrease 750 ml B2G1": "11.567",
    "Glim 750ml": "8.75",
    "Power Wash 500ml": "5.8",
    "Power Wash 1 Litre (pouch)": "21.99",
    "Power Wash 500ml B2G1": "7.867",
    "Rhino 250ml": "5.234",
    "Rhino 500ml": "17.4",
    "Rhino 750ml": "9.17",
    "Titan 500 g": "5.456",
    "Titan 1.25 kg": "11.37",
    "Washout Multi-surface Disinfectant Floral Red": "11.395",
    "Washout Multi-surface Disinfectant Lemon Yellow": "11.395",
    "Washout Multi-surface Disinfectant Ocean Blue": "11.395",
    "Washout B2G1 (Floral + Ocean + Lemon)": "15.567",
    "Brighten Laundry Detergent + Fabrito Fabric Softener bundle (1 litre each)": "11.22",
    "Power Wash Dish Wash + Degrease Spray Bundle": "6.795",
    "Rhino 2x2 750ml": "8.99",
    # Rhino 250/500/750 ml B2G1: no standard weight given yet -> no check
}

# Liters of liquid per bottle. Bundle SKUs use component volumes via composition;
# multi-brand bundles and Titan powder stay null (free-text fill only).
FILL_VOLUME_LITERS = {
    "Brighten Laundry Detergent (pouch)(1 litre)": "1.000",
    "Brighten Liquid Laundry Detergent (1 litre)": "1.000",
    "Fabrito Fabric Softener (1 litre)": "1.000",
    "Fabrito Fabric Softener (pouch)(1 litre)": "1.000",
    "Degrease Spray 750ml": "0.750",
    "Glim 750ml": "0.750",
    "Power Wash 500ml": "0.500",
    "Power Wash 1 Litre (pouch)": "1.000",
    "Rhino 250ml": "0.250",
    "Rhino 500ml": "0.500",
    "Rhino 750ml": "0.750",
    "Washout Multi-surface Disinfectant Floral Red": "1.000",
    "Washout Multi-surface Disinfectant Lemon Yellow": "1.000",
    "Washout Multi-surface Disinfectant Ocean Blue": "1.000",
    # Same-product B2G1 / Rhino 2x2: fill math uses component product volumes
}


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

        parents = {bp.code: bp for bp in BatchProduct.objects.all()}
        sheet_names = set()
        for name, units, unit_label, order in SHEET_PRODUCTS:
            sheet_names.add(name)
            code = batch_product_code_for(name)
            Product.objects.update_or_create(
                name=name,
                defaults={
                    "bottles_per_carton": units,
                    "unit_label": unit_label,
                    "show_on_sheet": True,
                    "is_active": True,
                    "sort_order": order,
                    "batch_product": parents.get(code) if code else None,
                    "standard_carton_weight_kg": (
                        Decimal(STANDARD_CARTON_WEIGHT_KG[name])
                        if name in STANDARD_CARTON_WEIGHT_KG
                        else None
                    ),
                    "fill_volume_liters": (
                        Decimal(FILL_VOLUME_LITERS[name])
                        if name in FILL_VOLUME_LITERS
                        else None
                    ),
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
