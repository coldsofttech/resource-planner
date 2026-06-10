from __future__ import annotations

import datetime

from django.db.models import Count, Max, Min, QuerySet

from apps.holidays.models import Holiday


def get_all_holidays() -> QuerySet[Holiday]:
    return Holiday.objects.select_related("location", "created_by", "updated_by").all()


def get_holiday_by_code(code: str) -> Holiday | None:
    try:
        return Holiday.objects.select_related(
            "location", "created_by", "updated_by"
        ).get(code=code)
    except Holiday.DoesNotExist:
        return None


def holiday_exists(
    location_id: int,
    date: datetime.date,
    exclude_pk: int | None = None,
) -> bool:
    qs = Holiday.objects.filter(location_id=location_id, date=date)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_holiday_options() -> QuerySet[Holiday]:
    return (
        Holiday.objects.select_related("location")
        .only(
            "code",
            "name",
            "date",
            "location__code",
            "location__city",
            "location__country",
        )
        .order_by("location", "date")
    )


def get_holiday_stats() -> dict:
    return Holiday.objects.aggregate(total=Count("id"))


def get_holiday_year_range() -> tuple[int, int] | None:
    result = Holiday.objects.aggregate(min_date=Min("date"), max_date=Max("date"))
    min_date = result.get("min_date")
    max_date = result.get("max_date")
    if min_date is None or max_date is None:
        return None
    return (min_date.year, max_date.year)
