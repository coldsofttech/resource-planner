from decimal import Decimal

from django.db import models

from apps.core.models import TimeStampedModel, unique_constraint


class EngineerHirePlaceholderAbsence(TimeStampedModel):
    placeholder_engineer = models.ForeignKey(
        "resource_plans.EngineerHirePlaceholder",
        on_delete=models.CASCADE,
        related_name="absences",
    )
    sprint = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.PROTECT,
        related_name="engineer_hire_placeholder_absences",
    )
    days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_engine_generated = models.BooleanField(default=True)
    override_days = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    override_notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["placeholder_engineer", "sprint"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="engineerhireplaceholderabsence",
                fields=["placeholder_engineer", "sprint"],
            )
        ]

    @property
    def effective_days(self) -> Decimal:
        if self.override_days is not None:
            return self.override_days
        return self.days

    def __str__(self) -> str:
        return f"{self.placeholder_engineer} — {self.sprint}"
