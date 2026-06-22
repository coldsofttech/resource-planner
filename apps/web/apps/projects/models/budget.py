from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.financial_years.models import FinancialYear
from apps.projects.constants import ProjectBudgetAction

from .estimate import ProjectEstimate
from .project import Project


def _get_size_for_amount(amount: float) -> str:
    from apps.configurations.selectors import Project as ProjectConfig

    if amount <= ProjectConfig.get_size_xs_max_amount():
        return "XS"
    if amount <= ProjectConfig.get_size_s_max_amount():
        return "S"
    if amount <= ProjectConfig.get_size_m_max_amount():
        return "M"
    if amount <= ProjectConfig.get_size_l_max_amount():
        return "L"
    return "XL"


def _compute_risk(
    actual_budget: float | None,
    estimate_total_cost: float | None,
) -> dict | None:
    if actual_budget is None or estimate_total_cost is None:
        return None
    try:
        actual = Decimal(str(actual_budget))
        cost = Decimal(str(estimate_total_cost))
    except (InvalidOperation, TypeError):
        return None
    if actual == 0 or cost == 0:
        return None

    from apps.configurations.selectors import Project as ProjectConfig

    threshold = Decimal(str(ProjectConfig.get_budget_risk_threshold()))
    size = _get_size_for_amount(float(actual))
    _size_variance = {
        "XS": ProjectConfig.get_size_xs_budget_variance,
        "S": ProjectConfig.get_size_s_budget_variance,
        "M": ProjectConfig.get_size_m_budget_variance,
        "L": ProjectConfig.get_size_l_budget_variance,
        "XL": ProjectConfig.get_size_xl_budget_variance,
    }
    green_pct = Decimal(str(_size_variance[size]()))

    variance_pct = (cost - actual) / actual * 100
    sign = "+" if variance_pct >= 0 else ""
    percentage = f"{sign}{variance_pct:.2f}"
    abs_variance = abs(variance_pct)

    if abs_variance <= green_pct:
        return {
            "color": "GREEN",
            "display": "On Budget",
            "short": "OB",
            "percentage": percentage,
        }
    if abs_variance <= threshold:
        if variance_pct > 0:
            return {
                "color": "AMBER",
                "display": "At Risk (Over)",
                "short": "AR+",
                "percentage": percentage,
            }
        return {
            "color": "AMBER",
            "display": "At Risk (Under)",
            "short": "AR-",
            "percentage": percentage,
        }
    if variance_pct > 0:
        return {
            "color": "RED",
            "display": "Over Budget",
            "short": "OVR",
            "percentage": percentage,
        }
    return {
        "color": "RED",
        "display": "Under Budget",
        "short": "UND",
        "percentage": percentage,
    }


class ProjectBudget(CodeModel, AuditableModel):
    MODEL_CODE = "PROJBGT"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="budgets",
        db_index=True,
    )
    financial_year = models.ForeignKey(
        FinancialYear,
        on_delete=models.PROTECT,
        related_name="project_budgets",
        db_index=True,
    )
    allocated_budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    refined_budget = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    estimate_version = models.ForeignKey(
        ProjectEstimate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="budgets",
        db_index=True,
    )
    note = models.TextField(blank=True, default="")

    @property
    def actual_budget(self) -> float:
        val = (
            self.refined_budget
            if self.refined_budget is not None
            else self.allocated_budget
        )
        return float(val)

    @property
    def remaining_budget(self) -> float | None:
        actual = self.actual_budget
        if actual is None:
            return None
        if self.estimate_version is None:
            return actual
        return round(actual - self.estimate_version.total_cost, 2)

    @property
    def risk(self) -> dict | None:
        estimate_cost = (
            float(self.estimate_version.total_cost) if self.estimate_version else None
        )
        return _compute_risk(self.actual_budget, estimate_cost)

    class Meta:
        ordering = ["project", "financial_year__start_date"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectbudget",
                fields=["project", "financial_year"],
            )
        ]
        permissions = [
            ("export_projectbudget", "Can export project budgets"),
        ]


class ProjectBudgetStatusHistory(models.Model):
    budget = models.ForeignKey(
        ProjectBudget,
        on_delete=models.CASCADE,
        related_name="status_history",
        db_index=True,
    )
    action = models.CharField(
        max_length=20,
        choices=ProjectBudgetAction.choices,
        db_index=True,
    )
    previous_allocated_budget = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    previous_refined_budget = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    previous_estimate_version = models.ForeignKey(
        ProjectEstimate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="budget_history_as_previous_estimate",
    )
    previous_total_cost = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    new_allocated_budget = models.DecimalField(max_digits=14, decimal_places=2)
    new_refined_budget = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    new_estimate_version = models.ForeignKey(
        ProjectEstimate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="budget_history_as_new_estimate",
    )
    new_total_cost = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    note = models.TextField(blank=True, default="")
    changed_on = models.DateTimeField(auto_now_add=True, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_budget_status_changes",
    )

    class Meta:
        ordering = ["-changed_on"]
