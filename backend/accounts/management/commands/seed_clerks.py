from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Seed portal users (order clerks, Esha, Ali, Rashid)"

    def handle(self, *args, **options):
        # (username, first_name, password, role, can_market_visit)
        users = [
            ("ahtisham", "Ahtisham", "Clerk123!", User.Role.ORDER_CLERK, True),
            ("aslam", "Aslam", "Clerk123!", User.Role.ORDER_CLERK, True),
            ("nouman", "Nouman", "Clerk123!", User.Role.ORDER_CLERK, False),
            ("javeria", "Javeria", "Clerk123!", User.Role.ORDER_CLERK, False),
            ("esha", "Esha", "Clerk123!", User.Role.BATCH_CLERK, False),
            ("ali", "Ali", "Clerk123!", User.Role.DISPATCH_CLERK, False),
            ("rashid", "Rashid", "Clerk123!", User.Role.LOADING_CLERK, False),
        ]
        for username, first_name, password, role, can_market_visit in users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "role": role,
                    "is_staff": False,
                    "can_market_visit": can_market_visit,
                },
            )
            user.role = role
            user.first_name = first_name
            user.can_market_visit = can_market_visit
            user.set_password(password)
            user.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created user {username}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated user {username}"))
