from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ORDER_CLERK = "order_clerk", "Order Clerk"
        BATCH_CLERK = "batch_clerk", "Batch Clerk"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.ORDER_CLERK,
    )
    can_market_visit = models.BooleanField(
        default=False,
        help_text="If true, user can access the Market Visit tab (Ahtisham/Aslam).",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
