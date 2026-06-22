from django.db import models

from apps.core.models import AuditableModel, unique_constraint
from apps.sprints.models.sprint import Sprint
from apps.users.models import User


class Capacity(AuditableModel):
    sprint = models.ForeignKey(
        Sprint,
        on_delete=models.CASCADE,
        related_name="capacities",
        db_index=True,
    )
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sprint_capacities",
        db_index=True,
    )
    working_days = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    holiday_days = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    leave_days = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    net_capacity = models.DecimalField(max_digits=6, decimal_places=1, default=0)

    class Meta:
        ordering = ["sprint", "member"]
        constraints = [
            unique_constraint(
                app_label="sprints",
                model="capacity",
                fields=["sprint", "member"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.member} — {self.sprint} capacity"
