from django.db.models import Count, Q, QuerySet

from apps.projects.models import Programme


def get_all_programmes() -> QuerySet[Programme]:
    return Programme.objects.select_related("created_by", "updated_by").all()


def get_active_programmes() -> QuerySet[Programme]:
    return Programme.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_programme_by_code(code: str) -> Programme | None:
    try:
        return Programme.objects.select_related("created_by", "updated_by").get(
            code=code
        )
    except Programme.DoesNotExist:
        return None


def programme_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = Programme.objects.filter(name__iexact=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_programme_options() -> QuerySet[Programme]:
    return (
        Programme.objects.filter(is_active=True).only("code", "name").order_by("name")
    )


def get_programme_stats() -> dict:
    return Programme.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
