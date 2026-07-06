from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.resource_plans.constants import Progression, SegmentType


class PlanPhaseSegment(CodeModel, AuditableModel):
    MODEL_CODE = "RESSEGMENT"

    phase = models.ForeignKey(
        "resource_plans.PlanPhase",
        on_delete=models.CASCADE,
        related_name="segments",
    )
    # Server-computed append-only counter — never client-writable. There is no
    # edit/reorder UI for segments, so exposing this as an input would only
    # invite duplicate-order submission races.
    segment_order = models.PositiveIntegerField()
    segment_type = models.CharField(
        max_length=20,
        choices=SegmentType.choices,
        db_index=True,
    )
    # No end >= start constraint: a Ramp Down segment legitimately has end < start.
    start_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    end_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    progression = models.CharField(
        max_length=20,
        choices=Progression.choices,
        default=Progression.LINEAR,
    )
    duration = models.PositiveIntegerField()
    step_count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["phase", "segment_order"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="planphasesegment",
                fields=["phase", "segment_order"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.phase} — segment {self.segment_order}"
