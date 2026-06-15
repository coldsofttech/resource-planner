from django.db.models import QuerySet

from apps.projects.models import Project, ProjectTag


def get_all_project_tags(project: Project) -> QuerySet[ProjectTag]:
    return (
        ProjectTag.objects.select_related("tag", "created_by", "updated_by")
        .filter(project=project)
        .order_by("tag__name")
    )


def get_project_tag_by_code(code: str) -> ProjectTag | None:
    try:
        return ProjectTag.objects.select_related(
            "project", "tag", "created_by", "updated_by"
        ).get(code=code)
    except ProjectTag.DoesNotExist:
        return None


def project_tag_exists(project: Project, tag, exclude_pk: int | None = None) -> bool:
    qs = ProjectTag.objects.filter(project=project, tag=tag)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
