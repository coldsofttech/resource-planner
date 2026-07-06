from __future__ import annotations

from django.db.models import Count, Max, Q, QuerySet

from apps.sprints.constants import SprintStatus
from apps.sprints.models import Sprint


def get_all_sprints() -> QuerySet[Sprint]:
    return Sprint.objects.select_related(
        "financial_year", "created_by", "updated_by", "closed_by"
    ).all()


def get_active_sprints() -> QuerySet[Sprint]:
    return Sprint.objects.select_related(
        "financial_year", "created_by", "updated_by", "closed_by"
    ).filter(is_active=True)


def get_sprint_by_code(code: str) -> Sprint | None:
    try:
        return Sprint.objects.select_related(
            "financial_year", "created_by", "updated_by", "closed_by"
        ).get(code=code)
    except Sprint.DoesNotExist:
        return None


def get_sprint_by_number(sprint_number: int) -> Sprint | None:
    try:
        return Sprint.objects.select_related(
            "financial_year", "created_by", "updated_by", "closed_by"
        ).get(sprint_number=sprint_number)
    except Sprint.DoesNotExist:
        return None


def get_in_progress_sprint() -> Sprint | None:
    return (
        Sprint.objects.select_related(
            "financial_year", "created_by", "updated_by", "closed_by"
        )
        .filter(status=SprintStatus.IN_PROGRESS, is_active=True)
        .first()
    )


def get_sprints_for_fy(fy_code: str) -> QuerySet[Sprint]:
    return Sprint.objects.select_related(
        "financial_year", "created_by", "updated_by", "closed_by"
    ).filter(financial_year__code=fy_code)


def get_sprint_options(fy_code: str | None = None) -> QuerySet[Sprint]:
    qs = Sprint.objects.filter(is_active=True).only(
        "code",
        "sprint_number",
        "name",
        "start_date",
        "end_date",
        "month",
        "status",
        "financial_year_id",
    )
    if fy_code:
        qs = qs.filter(financial_year__code=fy_code)
    return qs.order_by("sprint_number")


def get_distinct_months_for_fy(fy_code: str) -> list[str]:
    """Distinct sprint months (YYYY-MM) for a financial year, in chronological order."""
    months: list[str] = []
    seen: set[str] = set()
    for month in (
        Sprint.objects.filter(financial_year__code=fy_code, is_active=True)
        .order_by("start_date")
        .values_list("month", flat=True)
    ):
        if month not in seen:
            seen.add(month)
            months.append(month)
    return months


def get_sprint_stats() -> dict:
    return Sprint.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
        in_progress=Count("id", filter=Q(status=SprintStatus.IN_PROGRESS)),
        future=Count("id", filter=Q(status=SprintStatus.FUTURE)),
        completed=Count("id", filter=Q(status=SprintStatus.COMPLETED)),
        expired=Count("id", filter=Q(status=SprintStatus.EXPIRED)),
        closed=Count("id", filter=Q(is_closed=True)),
        overridden=Count("id", filter=Q(is_overridden=True)),
    )


def has_overlapping_sprint(
    start_date, end_date, fy_pk: int, exclude_pk: int | None = None
) -> bool:
    """Returns True if any sprint in the same FY overlaps with start_date..end_date."""
    qs = Sprint.objects.filter(
        financial_year_id=fy_pk,
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_max_sprint_number() -> int:
    result = Sprint.objects.aggregate(max_num=Max("sprint_number"))
    return result["max_num"] or 0


def get_sprints_overlapping_date(check_date) -> QuerySet[Sprint]:
    """Return sprints whose window contains check_date."""
    return Sprint.objects.filter(
        start_date__lte=check_date,
        end_date__gte=check_date,
        is_active=True,
    )


def get_sprints_overlapping_range(start_date, end_date) -> QuerySet[Sprint]:
    """Return sprints whose window overlaps the given date range."""
    return Sprint.objects.filter(
        start_date__lte=end_date,
        end_date__gte=start_date,
        is_active=True,
    )


def get_active_and_future_sprints() -> QuerySet[Sprint]:
    return Sprint.objects.filter(
        status__in=[SprintStatus.IN_PROGRESS, SprintStatus.FUTURE],
        is_active=True,
    )


def get_first_sprint_starting_on_or_after(fy_code: str, date) -> Sprint | None:
    return (
        Sprint.objects.select_related("financial_year")
        .filter(financial_year__code=fy_code, start_date__gte=date)
        .order_by("sprint_number")
        .first()
    )
