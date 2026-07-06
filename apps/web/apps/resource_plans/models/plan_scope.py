from django.db import models

from apps.core.models import AuditableModel


class PlanScope(AuditableModel):
    plan = models.OneToOneField(
        "resource_plans.Plan",
        on_delete=models.PROTECT,
        related_name="scope",
    )
    financial_year = models.ForeignKey(
        "financial_years.FinancialYear",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="plan_scopes",
    )
    programme = models.ForeignKey(
        "projects.Programme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="plan_scopes",
    )
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="plan_scopes",
    )
    team = models.ForeignKey(
        "teams.Team",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="plan_scopes",
    )

    class Meta:
        ordering = ["plan"]

    def __str__(self) -> str:
        return f"Scope for {self.plan}"
