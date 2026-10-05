from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Seed order clerk users for the shared portal"

    def handle(self, *args, **options):
        # (username, first_name, password, can_market_visit)
        clerks = [
            ("ahtisham", "Ahtisham", "Clerk123!", True),
            ("aslam", "Aslam", "Clerk123!", True),
            ("nouman", "Nouman", "Clerk123!", False),
            ("javeria", "Javeria", "Clerk123!", False),
        ]
        for username, first_name, password, can_market_visit in clerks:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "role": User.Role.ORDER_CLERK,
                    "is_staff": False,
                    "can_market_visit": can_market_visit,
                },
            )
            user.role = User.Role.ORDER_CLERK
            user.first_name = first_name
            user.can_market_visit = can_market_visit
            user.set_password(password)
            user.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created user {username}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated user {username}"))
