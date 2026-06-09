from django.db.models import Count, Q, QuerySet

from apps.locations.models import Location


def get_all_locations() -> QuerySet[Location]:
    return Location.objects.select_related("created_by", "updated_by").all()


def get_active_locations() -> QuerySet[Location]:
    return Location.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_location_by_code(code: str) -> Location | None:
    try:
        return Location.objects.select_related("created_by", "updated_by").get(
            code=code
        )
    except Location.DoesNotExist:
        return None


def location_exists(city: str, country: str, exclude_pk: int | None = None) -> bool:
    qs = Location.objects.filter(city=city, country=country)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_location_options() -> QuerySet[Location]:
    return (
        Location.objects.filter(is_active=True)
        .only("code", "city", "country", "is_default")
        .order_by("country", "city")
    )


def get_location_stats() -> dict:
    return Location.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
