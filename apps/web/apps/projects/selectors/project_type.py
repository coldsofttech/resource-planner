from django.db.models import Count, Q, QuerySet

from apps.projects.models import ProjectType


def get_all_project_types() -> QuerySet[ProjectType]:
    return ProjectType.objects.select_related("created_by", "updated_by").all()


def get_active_project_types() -> QuerySet[ProjectType]:
    return ProjectType.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_project_type_by_code(code: str) -> ProjectType | None:
    try:
        return ProjectType.objects.select_related("created_by", "updated_by").get(
            code=code
        )
    except ProjectType.DoesNotExist:
        return None


def project_type_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = ProjectType.objects.filter(name__iexact=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_project_type_options() -> QuerySet[ProjectType]:
    return (
        ProjectType.objects.filter(is_active=True).only("code", "name").order_by("name")
    )


def get_project_type_stats() -> dict:
    return ProjectType.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
