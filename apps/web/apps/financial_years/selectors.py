from django.db.models import Count, Q, QuerySet

from apps.financial_years.constants import FinancialYearStatus
from apps.financial_years.models import FinancialYear


def get_all_financial_years() -> QuerySet[FinancialYear]:
    return FinancialYear.objects.select_related("created_by", "updated_by").all()


def get_active_financial_years() -> QuerySet[FinancialYear]:
    return FinancialYear.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_financial_year_by_code(code: str) -> FinancialYear | None:
    try:
        return FinancialYear.objects.select_related("created_by", "updated_by").get(
            code=code
        )
    except FinancialYear.DoesNotExist:
        return None


def get_in_progress_financial_year() -> FinancialYear | None:
    return (
        FinancialYear.objects.select_related("created_by", "updated_by")
        .filter(status=FinancialYearStatus.IN_PROGRESS, is_active=True)
        .first()
    )


def get_financial_year_options() -> QuerySet[FinancialYear]:
    return (
        FinancialYear.objects.filter(is_active=True)
        .only("code", "long_fy", "short_fy", "start_date", "end_date", "status")
        .order_by("-start_date")
    )


def get_financial_year_stats() -> dict:
    return FinancialYear.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
        in_progress=Count("id", filter=Q(status=FinancialYearStatus.IN_PROGRESS)),
        future=Count("id", filter=Q(status=FinancialYearStatus.FUTURE)),
        completed=Count("id", filter=Q(status=FinancialYearStatus.COMPLETED)),
        expired=Count("id", filter=Q(status=FinancialYearStatus.EXPIRED)),
    )


def has_overlapping_financial_year(
    start_date, end_date, exclude_pk: int | None = None
) -> bool:
    """Returns True if any existing FY date range overlaps with start_date..end_date."""
    qs = FinancialYear.objects.filter(
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
