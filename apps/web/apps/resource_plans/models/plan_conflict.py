from django.db import models

from apps.core.models import AuditableModel, CodeModel
from apps.resource_plans.constants import (
    ConflictResolutionType,
    ConflictSeverity,
    ConflictStatus,
    ConflictType,
)
from apps.users.models import User


class Conflict(CodeModel, AuditableModel):
    MODEL_CODE = "RESCONFLICT"

    allocation_set = models.ForeignKey(
        "resource_plans.AllocationSet",
        on_delete=models.CASCADE,
        related_name="conflicts",
    )
    engine_job = models.ForeignKey(
        "resource_plans.EngineJob",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="conflicts",
    )
    conflict_type = models.CharField(
        max_length=30,
        choices=ConflictType.choices,
        db_index=True,
    )
    severity = models.PositiveSmallIntegerField(
        choices=ConflictSeverity.choices,
        default=ConflictSeverity.ERROR,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=ConflictStatus.choices,
        default=ConflictStatus.OPEN,
        db_index=True,
    )
    # Informational "what triggered this" pointers — not ownership.
    affected_project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resource_plan_conflicts",
    )
    affected_phase = models.ForeignKey(
        "resource_plans.PlanPhase",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="conflicts",
    )
    affected_member = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resource_plan_conflicts",
    )
    affected_sprint = models.ForeignKey(
        "sprints.Sprint",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resource_plan_conflicts",
    )
    affected_team = models.ForeignKey(
        "teams.Team",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resource_plan_conflicts",
    )
    description = models.TextField(blank=True, default="")
    engine_data = models.JSONField(default=dict, blank=True)
    resolution_type = models.CharField(
        max_length=30,
        choices=ConflictResolutionType.choices,
        null=True,
        blank=True,
    )
    resolution_notes = models.TextField(blank=True, default="")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["severity", "-created_at"]

    def __str__(self) -> str:
        return f"{self.get_conflict_type_display()} — {self.get_severity_display()}"
