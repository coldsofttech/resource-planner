from __future__ import annotations

from django.db.models import QuerySet

from apps.projects.models import Project
from apps.resource_plans.models import PlanVersion, PlanVersionProject


def get_unmapped_projects(version: PlanVersion) -> QuerySet[Project]:
    return (
        Project.objects.filter(is_active=True)
        .exclude(resource_plan_versions__version=version)
        .select_related("programme")
        .order_by("name")
    )


def get_configured_projects(version: PlanVersion) -> QuerySet[PlanVersionProject]:
    return (
        PlanVersionProject.objects.filter(version=version)
        .select_related(
            "project",
            "project__programme",
            "snapshotted_budget",
            "snapshotted_estimate",
        )
        .order_by("project__name")
    )


def get_version_project_by_code(code: str) -> PlanVersionProject | None:
    try:
        return PlanVersionProject.objects.select_related(
            "version",
            "version__plan",
            "version__plan__financial_year",
            "project",
            "snapshotted_budget",
            "snapshotted_estimate",
            "start_sprint",
            "end_sprint",
            "created_by",
            "updated_by",
        ).get(code=code)
    except PlanVersionProject.DoesNotExist:
        return None


def version_project_exists(version: PlanVersion, project: Project) -> bool:
    return PlanVersionProject.objects.filter(version=version, project=project).exists()
