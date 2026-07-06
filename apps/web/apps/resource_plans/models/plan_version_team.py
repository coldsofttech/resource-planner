from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.resource_plans.constants import AllocationType


class PlanVersionTeam(CodeModel, AuditableModel):
    MODEL_CODE = "RESVERT"

    plan_project = models.ForeignKey(
        "resource_plans.PlanVersionProject",
        on_delete=models.CASCADE,
        related_name="teams",
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="resource_plan_versions",
    )
    allocation_type = models.CharField(
        max_length=20,
        choices=AllocationType.choices,
        db_index=True,
    )
    allocation_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    allocation_days = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    allocation_budget = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    allocated_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sequence_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["plan_project", "sequence_order"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="planversionteam",
                fields=["plan_project", "team"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.plan_project} — {self.team}"
