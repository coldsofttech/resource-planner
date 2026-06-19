from __future__ import annotations

from django.db.models import QuerySet

from apps.projects.models import Project, ProjectAttachment


def get_attachment_by_code(code: str) -> ProjectAttachment | None:
    try:
        return ProjectAttachment.objects.select_related(
            "project",
            "created_by",
            "updated_by",
        ).get(code=code)
    except ProjectAttachment.DoesNotExist:
        return None


def get_attachments_for_project(project: Project) -> QuerySet[ProjectAttachment]:
    return (
        ProjectAttachment.objects.select_related(
            "project",
            "created_by",
            "updated_by",
        )
        .filter(project=project)
        .order_by("-created_at")
    )


def project_attachment_filename_exists(
    project: Project, file_name: str, exclude_pk: int | None = None
) -> bool:
    qs = ProjectAttachment.objects.filter(project=project, file_name=file_name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
