from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint

if TYPE_CHECKING:
    from apps.projects.models.project_actual_config import ProjectActualConfig


class ProjectActuals(CodeModel, AuditableModel):
    MODEL_CODE = "PROJAC"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="actuals",
        db_index=True,
    )
    fy = models.ForeignKey(
        "financial_years.FinancialYear",
        on_delete=models.CASCADE,
        related_name="project_actuals",
        db_index=True,
    )
    total_cost_to_date = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
    )
    prev_fy_actuals = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
    )

    def _get_actuals_config(self) -> ProjectActualConfig | None:
        from apps.projects.models.project_actual_config import ProjectActualConfig

        return ProjectActualConfig.objects.filter(project_id=self.project_id).first()

    def _get_approved_estimate_costs(
        self,
    ) -> tuple[Decimal, Decimal] | None:
        """Return (base_cost, cost_with_contingency) for the current approved estimate.

        Returns None when no approved estimate exists.
        """
        from apps.projects.constants import ProjectEstimateStatus
        from apps.projects.models.estimate import ProjectEstimate

        estimate = (
            ProjectEstimate.objects.filter(
                project_id=self.project_id,
                status=ProjectEstimateStatus.APPROVED,
            )
            .order_by("-version")
            .first()
        )
        if estimate is None:
            return None

        base = Decimal(str(estimate.estimate_days)) * Decimal(str(estimate.day_rate))
        contingency = (
            base * Decimal(str(estimate.contingency_percentage)) / Decimal("100")
        )
        return base, base + contingency

    @property
    def remaining_amount(self) -> Decimal | None:
        config = self._get_actuals_config()
        costs = self._get_approved_estimate_costs()
        if costs is None:
            return None
        base, base_with_contingency = costs
        ignore_prev = config.ignore_prev_fy_actuals if config else False
        total = (
            self.total_cost_to_date
            if ignore_prev
            else self.total_cost_to_date + self.prev_fy_actuals
        )
        if total <= base:
            return base - total
        return base_with_contingency - total

    @property
    def risk(self) -> str | None:
        from apps.projects.constants import ActualsRiskType

        config = self._get_actuals_config()
        if config and config.ignore_risk:
            return None
        costs = self._get_approved_estimate_costs()
        if costs is None:
            return None
        base, base_with_contingency = costs
        if base <= 0:
            return None
        ignore_prev = config.ignore_prev_fy_actuals if config else False
        total = (
            self.total_cost_to_date
            if ignore_prev
            else self.total_cost_to_date + self.prev_fy_actuals
        )
        if total <= base:
            return None
        if total <= base_with_contingency:
            return ActualsRiskType.WARNING  # type: ignore[return-value]
        return ActualsRiskType.AT_RISK  # type: ignore[return-value]

    class Meta:
        ordering = ["project", "fy"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectactuals",
                fields=["project", "fy"],
            )
        ]
