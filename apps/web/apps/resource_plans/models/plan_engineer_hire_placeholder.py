from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.users.models import User


class EngineerHirePlaceholder(CodeModel, AuditableModel):
    MODEL_CODE = "RESHIRE"

    version = models.ForeignKey(
        "resource_plans.PlanVersion",
        on_delete=models.CASCADE,
        related_name="engineer_hire_placeholders",
    )
    sequence_number = models.PositiveIntegerField()
    display_name = models.CharField(max_length=255)
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="engineer_hire_placeholders",
    )
    manpower_request = models.ForeignKey(
        "resource_plans.ManpowerRequest",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="engineer_hire_placeholders",
    )
    onboard_sprint = models.ForeignKey(
        "sprints.Sprint",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="engineer_hire_placeholders_onboarding",
    )
    engine_suggested_sprint = models.ForeignKey(
        "sprints.Sprint",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="engineer_hire_placeholders_suggested",
    )
    capacity_days_per_sprint = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    replaced_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="engineer_hire_placeholders_replaced",
    )
    replaced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["version", "sequence_number"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="engineerhireplaceholder",
                fields=["version", "sequence_number"],
            )
        ]

    def __str__(self) -> str:
        return self.display_name
