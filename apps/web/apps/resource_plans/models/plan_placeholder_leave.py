from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.users.models import User


class PlaceholderLeave(CodeModel, AuditableModel):
    MODEL_CODE = "RESPLV"

    version = models.ForeignKey(
        "resource_plans.PlanVersion",
        on_delete=models.CASCADE,
        related_name="placeholder_leaves",
    )
    member = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="placeholder_leaves",
    )
    sprint = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.PROTECT,
        related_name="placeholder_leaves",
    )
    days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_auto = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["version", "member", "sprint"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="placeholderleave",
                fields=["version", "member", "sprint"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.version} — {self.member} — {self.sprint}"
