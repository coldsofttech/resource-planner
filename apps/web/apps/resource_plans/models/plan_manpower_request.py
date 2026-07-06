from django.db import models

from apps.core.models import AuditableModel, CodeModel
from apps.resource_plans.constants import ManpowerRequestStatus


class ManpowerRequest(CodeModel, AuditableModel):
    MODEL_CODE = "RESMANPOWER"

    allocation_set = models.ForeignKey(
        "resource_plans.AllocationSet",
        on_delete=models.CASCADE,
        related_name="manpower_requests",
    )
    conflict = models.ForeignKey(
        "resource_plans.Conflict",
        on_delete=models.CASCADE,
        related_name="manpower_requests",
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="manpower_requests",
    )
    phase = models.ForeignKey(
        "resource_plans.PlanPhase",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="manpower_requests",
    )
    sprints_needed = models.PositiveIntegerField()
    days_needed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=ManpowerRequestStatus.choices,
        default=ManpowerRequestStatus.OPEN,
        db_index=True,
    )
    resolution_notes = models.TextField(blank=True, default="")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.team} — {self.get_status_display()}"
