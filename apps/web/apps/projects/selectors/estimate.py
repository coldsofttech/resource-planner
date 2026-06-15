from __future__ import annotations

from django.db.models import Max, QuerySet

from apps.projects.models import Project, ProjectEstimate, ProjectEstimateStatusHistory


def get_estimate_by_code(code: str) -> ProjectEstimate | None:
    try:
        return (
            ProjectEstimate.objects.select_related(
                "project",
                "project__programme",
                "created_by",
                "updated_by",
            )
            .prefetch_related("shared_by", "reviewed_by")
            .get(code=code)
        )
    except ProjectEstimate.DoesNotExist:
        return None


def get_estimates_for_project(project: Project) -> QuerySet[ProjectEstimate]:
    return (
        ProjectEstimate.objects.select_related(
            "project",
            "created_by",
            "updated_by",
        )
        .prefetch_related("shared_by", "reviewed_by")
        .filter(project=project)
        .order_by("-version")
    )


def get_next_version(project: Project) -> int:
    result = ProjectEstimate.objects.filter(project=project).aggregate(
        max_version=Max("version")
    )
    return (result["max_version"] or 0) + 1


def get_estimate_status_history(
    estimate: ProjectEstimate,
) -> QuerySet[ProjectEstimateStatusHistory]:
    return (
        ProjectEstimateStatusHistory.objects.select_related("changed_by")
        .filter(estimate=estimate)
        .order_by("-changed_on")
    )
