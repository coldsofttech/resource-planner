from django.db.models import Count, Q, QuerySet

from apps.employment_types.models import EmploymentType


def get_all_employment_types() -> QuerySet[EmploymentType]:
    return EmploymentType.objects.select_related("created_by", "updated_by").all()


def get_active_employment_types() -> QuerySet[EmploymentType]:
    return EmploymentType.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_employment_type_by_code(code: str) -> EmploymentType | None:
    try:
        return EmploymentType.objects.select_related("created_by", "updated_by").get(
            code=code
        )
    except EmploymentType.DoesNotExist:
        return None


def employment_type_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = EmploymentType.objects.filter(name=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_employment_type_options() -> QuerySet[EmploymentType]:
    return (
        EmploymentType.objects.filter(is_active=True)
        .only("code", "name", "is_default")
        .order_by("name")
    )


def get_employment_type_stats() -> dict:
    return EmploymentType.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
