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
