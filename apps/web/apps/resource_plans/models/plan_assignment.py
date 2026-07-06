from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.resource_plans.constants import AssignmentType
from apps.users.models import User


class PlanAssignment(CodeModel, AuditableModel):
    MODEL_CODE = "RESASSIGN"

    phase = models.ForeignKey(
        "resource_plans.PlanPhase",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    member = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="plan_assignments",
    )
    auto_assign = models.BooleanField(default=False)
    assignment_type = models.CharField(
        max_length=20,
        choices=AssignmentType.choices,
        db_index=True,
    )
    # Interim-only fields — who this assignment is covering for, and for how long.
    replaces_member = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="plan_assignments_replaced",
    )
    interim_sprint_count = models.PositiveIntegerField(null=True, blank=True)
    # Relevant when the phase's split_mode is Percent or Days; optional otherwise.
    split_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    # Always server-computed from assignment_type — never client-writable.
    includes_in_budget = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["phase", "id"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="planassignment",
                fields=["phase", "member", "assignment_type"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.phase} — {self.member}"
