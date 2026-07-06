from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.resource_plans.constants import DependencyType


class PlanPhaseDependency(CodeModel, AuditableModel):
    MODEL_CODE = "RESDEP"

    phase = models.ForeignKey(
        "resource_plans.PlanPhase",
        on_delete=models.CASCADE,
        related_name="dependencies",
    )
    # Predecessor may belong to any team/project within the same plan version
    # (see the UI mockup on GH #173 — the picker groups options by project).
    predecessor_phase = models.ForeignKey(
        "resource_plans.PlanPhase",
        on_delete=models.CASCADE,
        related_name="dependent_on",
    )
    dependency_type = models.CharField(
        max_length=20,
        choices=DependencyType.choices,
        db_index=True,
    )
    # Signed: negative represents lead time (starting before the strict lag boundary).
    lag_sprints = models.IntegerField(default=0)

    class Meta:
        ordering = ["phase", "id"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="planphasedependency",
                fields=["phase", "predecessor_phase"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.phase} depends on {self.predecessor_phase}"
