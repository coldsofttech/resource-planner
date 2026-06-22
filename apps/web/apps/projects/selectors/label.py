from django.db import models
from django.db.models import QuerySet

from apps.projects.models import Project, ProjectLabel


def get_all_system_labels() -> list[str]:
    return list(ProjectLabel.objects.values_list("label", flat=True).order_by("label"))


def get_sibling_labels(programme_name: str) -> list[str]:
    return list(
        ProjectLabel.objects.filter(project__programme__name=programme_name)
        .values_list("label", flat=True)
        .order_by("label")
    )


def get_all_labels_as_options() -> list[dict]:
    return list(
        ProjectLabel.objects.select_related("project")
        .order_by("project__name", "label")
        .values("code", "label", project_name=models.F("project__name"))
    )


def get_all_project_labels(project: Project) -> QuerySet[ProjectLabel]:
    return (
        ProjectLabel.objects.select_related("created_by", "updated_by")
        .filter(project=project)
        .order_by("-is_default", "label")
    )


def get_project_label_by_code(code: str) -> ProjectLabel | None:
    try:
        return ProjectLabel.objects.select_related(
            "project", "created_by", "updated_by"
        ).get(code=code)
    except ProjectLabel.DoesNotExist:
        return None


def project_label_exists(
    project: Project, label: str, exclude_pk: int | None = None
) -> bool:
    qs = ProjectLabel.objects.filter(project=project, label__iexact=label)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_project_default_label(project: Project) -> ProjectLabel | None:
    return ProjectLabel.objects.filter(project=project, is_default=True).first()
