from django.db import models

from apps.core.models import TimeStampedModel, unique_constraint
from apps.users.models import User


class MemberCapacity(TimeStampedModel):
    version = models.ForeignKey(
        "resource_plans.PlanVersion",
        on_delete=models.CASCADE,
        related_name="member_capacities",
    )
    member = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="member_capacities",
    )
    sprint = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.PROTECT,
        related_name="member_capacities",
    )
    working_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    holiday_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    leave_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    placeholder_leave_days = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    net_capacity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["version", "member", "sprint"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="membercapacity",
                fields=["version", "member", "sprint"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.version} — {self.member} — {self.sprint}"
