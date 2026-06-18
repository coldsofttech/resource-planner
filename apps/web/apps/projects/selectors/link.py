from __future__ import annotations

from django.db.models import QuerySet

from apps.projects.models import Project, ProjectLink


def get_link_by_code(code: str) -> ProjectLink | None:
    try:
        return ProjectLink.objects.select_related(
            "project",
            "created_by",
            "updated_by",
        ).get(code=code)
    except ProjectLink.DoesNotExist:
        return None


def get_links_for_project(project: Project) -> QuerySet[ProjectLink]:
    return (
        ProjectLink.objects.select_related(
            "project",
            "created_by",
            "updated_by",
        )
        .filter(project=project)
        .order_by("title")
    )


def project_link_title_exists(
    project: Project, title: str, exclude_pk: int | None = None
) -> bool:
    qs = ProjectLink.objects.filter(project=project, title=title)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
