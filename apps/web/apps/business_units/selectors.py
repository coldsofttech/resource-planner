from django.db.models import Count, Q, QuerySet

from apps.business_units.models import BusinessUnit


def get_all_business_units() -> QuerySet[BusinessUnit]:
    return BusinessUnit.objects.select_related("created_by", "updated_by").all()


def get_active_business_units() -> QuerySet[BusinessUnit]:
    return BusinessUnit.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_business_unit_by_code(code: str) -> BusinessUnit | None:
    try:
        return BusinessUnit.objects.select_related("created_by", "updated_by").get(
            code=code
        )
    except BusinessUnit.DoesNotExist:
        return None


def business_unit_name_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = BusinessUnit.objects.filter(name=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_business_unit_stats() -> dict:
    return BusinessUnit.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
