from django.core.management.base import BaseCommand

from batches.models import BatchProduct

PARENTS = [
    ("rhino", "Rhino", 1),
    ("brighten", "Brighten", 2),
    ("fabrito", "Fabrito", 3),
    ("degrease", "Degrease", 4),
    ("glim", "Glim", 5),
    ("titan", "Titan", 6),
    ("washout_lemon", "Washout Lemon", 7),
    ("washout_floral", "Washout Floral", 8),
    ("washout_ocean", "Washout Ocean", 9),
]


class Command(BaseCommand):
    help = "Seed parent batch products for Esha portal"

    def handle(self, *args, **options):
        codes = set()
        for code, name, order in PARENTS:
            codes.add(code)
            BatchProduct.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "is_active": True,
                    "sort_order": order,
                },
            )
        deactivated = (
            BatchProduct.objects.exclude(code__in=codes)
            .filter(is_active=True)
            .update(is_active=False)
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(codes)} batch products ({deactivated} deactivated)."
            )
        )
