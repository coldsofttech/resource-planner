from django.db import models

from apps.core.models import TimeStampedModel, unique_constraint
from apps.resource_plans.constants import EngineJobStatus, EngineJobStepName


class EngineJobStep(TimeStampedModel):
    job = models.ForeignKey(
        "resource_plans.EngineJob",
        on_delete=models.CASCADE,
        related_name="steps",
        db_index=True,
    )
    step_order = models.PositiveIntegerField()
    name = models.CharField(max_length=50, choices=EngineJobStepName.choices)
    status = models.CharField(
        max_length=20,
        choices=EngineJobStatus.choices,
        default=EngineJobStatus.PENDING,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_milliseconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["job", "step_order"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="enginejobstep",
                fields=["job", "step_order"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.job} — {self.name}"
