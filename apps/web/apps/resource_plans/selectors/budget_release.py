from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import PlanBudgetRelease, PlanVersionProject
from apps.sprints.models import Sprint


def get_budget_releases_for_project(
    plan_version_project: PlanVersionProject,
) -> QuerySet[PlanBudgetRelease]:
    return PlanBudgetRelease.objects.filter(
        plan_version_project=plan_version_project
    ).select_related("sprint")


def get_budget_release_by_code(code: str) -> PlanBudgetRelease | None:
    try:
        return PlanBudgetRelease.objects.select_related(
            "plan_version_project",
            "plan_version_project__version",
            "plan_version_project__version__plan",
            "sprint",
        ).get(code=code)
    except PlanBudgetRelease.DoesNotExist:
        return None


def get_locked_entry_type_for_project(
    plan_version_project: PlanVersionProject,
) -> str | None:
    return (
        PlanBudgetRelease.objects.filter(plan_version_project=plan_version_project)
        .values_list("entry_type", flat=True)
        .first()
    )


def budget_release_exists_for_sprint(
    plan_version_project: PlanVersionProject,
    sprint: Sprint,
    exclude_pk: int | None = None,
) -> bool:
    qs = PlanBudgetRelease.objects.filter(
        plan_version_project=plan_version_project, sprint=sprint
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def budget_release_exists_for_month(
    plan_version_project: PlanVersionProject,
    month: str,
    exclude_pk: int | None = None,
) -> bool:
    qs = PlanBudgetRelease.objects.filter(
        plan_version_project=plan_version_project, month=month
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
