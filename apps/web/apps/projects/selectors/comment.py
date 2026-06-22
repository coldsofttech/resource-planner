from __future__ import annotations

from django.db.models import QuerySet

from apps.projects.models import Project, ProjectComment


def get_all_project_comments(project: Project) -> QuerySet[ProjectComment]:
    return (
        ProjectComment.objects.select_related(
            "comment__created_by__profile",
            "comment__updated_by__profile",
        )
        .prefetch_related("comment__mentions__user")
        .filter(project=project)
        .order_by("-comment__is_pinned", "-comment__created_at")
    )


def get_pinned_project_comments_count(project: Project) -> int:
    return ProjectComment.objects.filter(
        project=project, comment__is_pinned=True
    ).count()


def get_project_comment_by_code(code: str) -> ProjectComment | None:
    try:
        return (
            ProjectComment.objects.select_related(
                "project",
                "comment__created_by__profile",
                "comment__updated_by__profile",
            )
            .prefetch_related("comment__mentions__user")
            .get(code=code)
        )
    except ProjectComment.DoesNotExist:
        return None
