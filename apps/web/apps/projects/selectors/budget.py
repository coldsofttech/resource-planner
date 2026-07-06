from __future__ import annotations

from django.db.models import QuerySet

from apps.financial_years.models import FinancialYear
from apps.projects.models import Project, ProjectBudget, ProjectBudgetStatusHistory


def get_budget_by_code(code: str) -> ProjectBudget | None:
    try:
        return ProjectBudget.objects.select_related(
            "project",
            "project__programme",
            "financial_year",
            "estimate_version",
            "created_by",
            "updated_by",
        ).get(code=code)
    except ProjectBudget.DoesNotExist:
        return None


def get_budgets_for_project(project: Project) -> QuerySet[ProjectBudget]:
    return (
        ProjectBudget.objects.select_related(
            "project",
            "financial_year",
            "estimate_version",
            "created_by",
            "updated_by",
        )
        .filter(project=project)
        .order_by("-financial_year__start_date")
    )


def get_budget_for_project_and_fy(
    project: Project,
    financial_year: FinancialYear,
) -> ProjectBudget | None:
    try:
        return ProjectBudget.objects.select_related(
            "project",
            "financial_year",
            "estimate_version",
        ).get(project=project, financial_year=financial_year)
    except ProjectBudget.DoesNotExist:
        return None


def budget_exists_for_project_and_fy(
    project: Project,
    financial_year: FinancialYear,
    exclude_pk: int | None = None,
) -> bool:
    qs = ProjectBudget.objects.filter(project=project, financial_year=financial_year)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_budget_status_history(
    budget: ProjectBudget,
) -> QuerySet[ProjectBudgetStatusHistory]:
    return (
        ProjectBudgetStatusHistory.objects.select_related(
            "previous_estimate_version",
            "new_estimate_version",
            "changed_by",
        )
        .filter(budget=budget)
        .order_by("-changed_on")
    )


def get_lifetime_budget_summary(project: Project) -> dict:
    from apps.projects.models.budget import _compute_risk

    budgets = list(
        ProjectBudget.objects.select_related("estimate_version").filter(project=project)
    )

    budget_count = len(budgets)
    total_allocated = sum(float(b.allocated_budget) for b in budgets)

    refined_values = [
        float(b.refined_budget) for b in budgets if b.refined_budget is not None
    ]
    total_refined: float | None = sum(refined_values) if refined_values else None

    total_actual = sum(b.actual_budget for b in budgets)

    estimate_values = [
        float(b.estimate_version.total_cost)
        for b in budgets
        if b.estimate_version is not None
    ]
    total_estimate: float | None = sum(estimate_values) if estimate_values else None

    total_remaining: float | None = (
        round(total_actual - total_estimate, 2) if total_estimate is not None else None
    )

    risk = _compute_risk(total_actual if total_actual else None, total_estimate)

    return {
        "project_code": project.code,
        "project_name": project.name,
        "budget_count": budget_count,
        "total_allocated_budget": total_allocated,
        "total_refined_budget": total_refined,
        "total_actual_budget": total_actual,
        "total_estimate_cost": total_estimate,
        "total_remaining_budget": total_remaining,
        "risk": risk,
    }
