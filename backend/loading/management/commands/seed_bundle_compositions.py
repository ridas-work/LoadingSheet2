from django.core.management.base import BaseCommand

from catalog.models import Product
from loading.models import BundleComposition

# bundle_name -> [(component_name, qty_per_set), ...]
COMPOSITIONS = {
    "Rhino 2x2 750ml": [("Rhino 750ml", 2)],
    "Brighten bottle B2G1": [("Brighten Liquid Laundry Detergent (1 litre)", 3)],
    "Fabrito bottle B2G1": [("Fabrito Fabric Softener (1 litre)", 3)],
    "Degrease 750 ml B2G1": [("Degrease Spray 750ml", 3)],
    "Power Wash 500ml B2G1": [("Power Wash 500ml", 3)],
    "Rhino 250 ml B2G1": [("Rhino 250ml", 3)],
    "Rhino 500 ml B2G1": [("Rhino 500ml", 3)],
    "Rhino 750 ml B2G1": [("Rhino 750ml", 3)],
    "Brighten Laundry Detergent + Fabrito Fabric Softener bundle (1 litre each)": [
        ("Brighten Liquid Laundry Detergent (1 litre)", 1),
        ("Fabrito Fabric Softener (1 litre)", 1),
    ],
    "Power Wash Dish Wash + Degrease Spray Bundle": [
        ("Power Wash 500ml", 1),
        ("Degrease Spray 750ml", 1),
    ],
    "Washout B2G1 (Floral + Ocean + Lemon)": [
        ("Washout Multi-surface Disinfectant Floral Red", 1),
        ("Washout Multi-surface Disinfectant Ocean Blue", 1),
        ("Washout Multi-surface Disinfectant Lemon Yellow", 1),
    ],
}


class Command(BaseCommand):
    help = "Seed bundle compositions for Ready stock entry"

    def handle(self, *args, **options):
        kept_ids = []
        created = 0
        for bundle_name, components in COMPOSITIONS.items():
            try:
                bundle = Product.objects.get(name=bundle_name, is_active=True)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Missing bundle: {bundle_name}"))
                continue
            for sort, (comp_name, qty) in enumerate(components):
                try:
                    component = Product.objects.get(name=comp_name, is_active=True)
                except Product.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Missing component for {bundle_name}: {comp_name}"
                        )
                    )
                    continue
                obj, was_created = BundleComposition.objects.update_or_create(
                    bundle_product=bundle,
                    component_product=component,
                    defaults={"qty_per_set": qty, "sort_order": sort},
                )
                kept_ids.append(obj.id)
                if was_created:
                    created += 1
        deleted, _ = (
            BundleComposition.objects.exclude(id__in=kept_ids).delete()
            if kept_ids
            else (0, {})
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Bundle compositions ready ({len(kept_ids)} rows, "
                f"{created} created, {deleted} removed)."
            )
        )
