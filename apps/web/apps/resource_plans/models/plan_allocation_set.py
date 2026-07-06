from django.db import models

from apps.core.models import AuditableModel, CodeModel
from apps.resource_plans.constants import AllocationSetStatus


class AllocationSet(CodeModel, AuditableModel):
    MODEL_CODE = "RESALLOCSET"

    version = models.ForeignKey(
        "resource_plans.PlanVersion",
        on_delete=models.CASCADE,
        related_name="allocation_sets",
    )
    engine_job = models.ForeignKey(
        "resource_plans.EngineJob",
        on_delete=models.PROTECT,
        related_name="allocation_sets",
    )
    status = models.CharField(
        max_length=20,
        choices=AllocationSetStatus.choices,
        default=AllocationSetStatus.DRAFT,
        db_index=True,
    )
    activated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.version} — {self.status}"
