from django.db import models

from apps.core.models import AuditableModel


class ProjectActualConfig(AuditableModel):
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="actuals_config",
    )
    ignore_risk = models.BooleanField(default=False)
    ignore_prev_fy_actuals = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["project"]
