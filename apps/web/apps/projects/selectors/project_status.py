from django.db.models import Count, Max, Q, QuerySet

from apps.projects.models import ProjectStatus, ProjectSubStatus


def get_all_project_statuses() -> QuerySet[ProjectStatus]:
    return ProjectStatus.objects.select_related("created_by", "updated_by").all()


def get_project_status_by_code(code: str) -> ProjectStatus | None:
    try:
        return ProjectStatus.objects.select_related("created_by", "updated_by").get(
            code=code
        )
    except ProjectStatus.DoesNotExist:
        return None


def get_project_status_options() -> QuerySet[ProjectStatus]:
    return (
        ProjectStatus.objects.filter(is_active=True)
        .only("code", "name", "sort_order")
        .order_by("sort_order", "name")
    )


def get_project_status_stats() -> dict:
    return ProjectStatus.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )


def get_all_project_sub_statuses() -> QuerySet[ProjectSubStatus]:
    return ProjectSubStatus.objects.select_related(
        "created_by", "updated_by", "main_status"
    ).all()


def get_project_sub_statuses_by_status(status_code: str) -> QuerySet[ProjectSubStatus]:
    return (
        ProjectSubStatus.objects.select_related(
            "created_by", "updated_by", "main_status"
        )
        .filter(main_status__code=status_code)
        .order_by("order", "name")
    )


def get_project_sub_status_by_code(code: str) -> ProjectSubStatus | None:
    try:
        return ProjectSubStatus.objects.select_related(
            "created_by", "updated_by", "main_status"
        ).get(code=code)
    except ProjectSubStatus.DoesNotExist:
        return None


def project_sub_status_exists(
    name: str, status: ProjectStatus, exclude_pk: int | None = None
) -> bool:
    qs = ProjectSubStatus.objects.filter(name__iexact=name, main_status=status)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_project_sub_status_options(
    status_code: str | None = None,
) -> QuerySet[ProjectSubStatus]:
    qs = ProjectSubStatus.objects.filter(is_active=True).select_related("main_status")
    if status_code:
        qs = qs.filter(main_status__code=status_code)
    return qs.order_by("main_status", "order", "name")


def get_project_sub_status_max_order(status: ProjectStatus) -> int:
    result = ProjectSubStatus.objects.filter(main_status=status).aggregate(Max("order"))
    return result["order__max"] or 0


def get_project_sub_status_stats(status_code: str | None = None) -> dict:
    qs = ProjectSubStatus.objects
    if status_code:
        qs = qs.filter(main_status__code=status_code)
    return qs.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
