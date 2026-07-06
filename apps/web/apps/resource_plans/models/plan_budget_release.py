from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.resource_plans.constants import BudgetReleaseEntryType


class PlanBudgetRelease(CodeModel, AuditableModel):
    MODEL_CODE = "RESBUDGET"

    plan_version_project = models.ForeignKey(
        "resource_plans.PlanVersionProject",
        on_delete=models.CASCADE,
        related_name="budget_releases",
    )
    entry_type = models.CharField(
        max_length=20,
        choices=BudgetReleaseEntryType.choices,
        db_index=True,
    )
    # Set when entry_type == Sprint; null when entry_type == Month.
    sprint = models.ForeignKey(
        "sprints.Sprint",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="plan_budget_releases",
    )
    # "YYYY-MM"; set when entry_type == Month, null when entry_type == Sprint.
    month = models.CharField(max_length=7, null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["plan_version_project", "id"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="planbudgetrelease",
                fields=["plan_version_project", "entry_type", "sprint", "month"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.plan_version_project} — {self.entry_type}"
