from django.db import models

from apps.core.models import CodeModel, TimeStampedModel, unique_constraint
from apps.resource_plans.constants import AssignmentType


class PlaceholderEngineer(CodeModel, TimeStampedModel):
    MODEL_CODE = "RESPLE"

    version = models.ForeignKey(
        "resource_plans.PlanVersion",
        on_delete=models.CASCADE,
        related_name="placeholder_engineers",
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="placeholder_engineers",
    )
    phase = models.ForeignKey(
        "resource_plans.PlanPhase",
        on_delete=models.CASCADE,
        related_name="placeholder_engineers",
    )
    slot_number = models.PositiveIntegerField(default=1)
    # Auto-generated from team + slot_number on first save — see save().
    name = models.CharField(max_length=255, blank=True)
    assignment_type = models.CharField(
        max_length=20,
        choices=AssignmentType.choices,
        default=AssignmentType.ENGINEER,
        db_index=True,
    )

    class Meta:
        ordering = ["version", "team", "slot_number"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="placeholderengineer",
                fields=["version", "team", "slot_number"],
            )
        ]

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.team.name} — Slot {self.slot_number}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
