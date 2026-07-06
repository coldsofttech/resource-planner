from django.db import models

from apps.core.models import AuditableModel, unique_constraint
from apps.resource_plans.constants import VersionStatus


class PlanVersion(AuditableModel):
    plan = models.ForeignKey(
        "resource_plans.Plan",
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=50,
        choices=VersionStatus.choices,
        default=VersionStatus.DRAFT,
        db_index=True,
    )
    cloned_from = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clones",
    )
    threshold_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,
    )
    has_leave_overrides = models.BooleanField(default=False)
    has_allocation_overrides = models.BooleanField(default=False)

    class Meta:
        ordering = ["plan", "version"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="planversion",
                fields=["plan", "version"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.plan} v{self.version}"
