from django.db import models

from apps.core.models import AuditableModel, CodeModel
from apps.resource_plans.constants import EngineJobMode, EngineJobStatus


class EngineJob(CodeModel, AuditableModel):
    MODEL_CODE = "RESENG"

    plan = models.ForeignKey(
        "resource_plans.Plan",
        on_delete=models.CASCADE,
        related_name="engine_jobs",
    )
    version = models.ForeignKey(
        "resource_plans.PlanVersion",
        on_delete=models.CASCADE,
        related_name="engine_jobs",
    )
    status = models.CharField(
        max_length=20,
        choices=EngineJobStatus.choices,
        default=EngineJobStatus.PENDING,
        db_index=True,
    )
    mode = models.CharField(
        max_length=20,
        choices=EngineJobMode.choices,
        default=EngineJobMode.VALIDATE,
        db_index=True,
    )
    current_step = models.CharField(max_length=50, blank=True, default="")
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    include_current_sprint = models.BooleanField(default=False)
    # Always server-computed from mode — never client-writable.
    dry_run = models.BooleanField(default=False)
    # Placeholder — functionality lands in a future issue.
    remove_overrides = models.BooleanField(default=False)
    initiated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_milliseconds = models.PositiveIntegerField(null=True, blank=True)
    validation_result = models.JSONField(default=dict, blank=True)
    steps_log = models.JSONField(default=list, blank=True)
    error_log = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-initiated_at"]

    def __str__(self) -> str:
        return f"{self.plan} — {self.mode} ({self.status})"
