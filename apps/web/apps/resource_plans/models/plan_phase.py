from decimal import Decimal

from django.db import models

from apps.core.models import AuditableModel, CodeModel, NamedModel, unique_constraint
from apps.resource_plans.constants import RampPattern, SplitMode


class PlanPhase(CodeModel, AuditableModel, NamedModel):
    MODEL_CODE = "RESPHASE"

    plan_project_team = models.ForeignKey(
        "resource_plans.PlanVersionTeam",
        on_delete=models.CASCADE,
        related_name="phases",
    )
    sequence_order = models.PositiveIntegerField(default=1)
    start_sprint = models.ForeignKey(
        "sprints.Sprint",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="plan_phases_started",
    )
    end_sprint = models.ForeignKey(
        "sprints.Sprint",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="plan_phases_ended",
    )
    max_days_per_sprint = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    ramp_pattern = models.CharField(
        max_length=20,
        choices=RampPattern.choices,
        default=RampPattern.FLAT,
        db_index=True,
    )
    allow_multiple_engineers = models.BooleanField(default=False)
    split_mode = models.CharField(
        max_length=20,
        choices=SplitMode.choices,
        default=SplitMode.AUTO,
    )
    # Maintained via recompute_is_split_incomplete() — no automatic hook
    # yet, see #185.
    is_split_incomplete = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    # Real ramp/segment-based calculation lands in #172 (PlanPhaseSegment).
    # No segments exist yet to derive this from, so it stays at 0 here.
    days_effort = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["plan_project_team", "sequence_order"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="planphase",
                fields=["plan_project_team", "name"],
            )
        ]

    def recompute_is_split_incomplete(self) -> None:
        if self.split_mode != SplitMode.PERCENT:
            incomplete = False
        else:
            total = sum(
                (a.split_value or Decimal("0"))
                for a in self.assignments.filter(split_value__isnull=False)
            )
            incomplete = abs(total - Decimal("100")) > Decimal("0.01")

        if incomplete != self.is_split_incomplete:
            self.is_split_incomplete = incomplete
            self.save(update_fields=["is_split_incomplete"])
