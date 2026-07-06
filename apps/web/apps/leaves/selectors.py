from __future__ import annotations

import datetime
from decimal import Decimal

from django.db.models import Count, QuerySet

from apps.leaves.models import Leave, LeaveDayEntry
from apps.users.models import User


def get_all_leaves() -> QuerySet[Leave]:
    return Leave.objects.select_related(
        "member",
        "member__profile",
        "created_by",
        "updated_by",
    ).all()


def get_leave_by_code(code: str) -> Leave | None:
    try:
        return Leave.objects.select_related(
            "member",
            "member__profile",
            "created_by",
            "updated_by",
        ).get(code=code)
    except Leave.DoesNotExist:
        return None


def leave_overlaps(
    member_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
    exclude_pk: int | None = None,
) -> bool:
    qs = Leave.objects.filter(
        member_id=member_id,
        end_date__gte=start_date,
        start_date__lte=end_date,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_leaves_affected_by_location_date_range(
    location_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
) -> QuerySet[Leave]:
    """
    Return leaves for members at location whose range overlaps the given date range.
    """
    return Leave.objects.filter(
        member__profile__location_id=location_id,
        start_date__lte=end_date,
        end_date__gte=start_date,
    ).select_related("member__profile")


def get_leave_stats() -> dict:
    return Leave.objects.aggregate(total=Count("id"))


def get_day_entries_for_leave(leave: Leave) -> QuerySet[LeaveDayEntry]:
    """Return all LeaveDayEntry rows for a leave, ordered by date."""
    return LeaveDayEntry.objects.filter(leave=leave).order_by("date")


def get_day_entries_for_member_in_range(
    member_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
) -> QuerySet[LeaveDayEntry]:
    """Return all LeaveDayEntry rows for a member within a date range.

    Joins through Leave so callers do not need to denormalize member onto
    the entry itself.
    """
    return (
        LeaveDayEntry.objects.filter(
            leave__member_id=member_id,
            date__gte=start_date,
            date__lte=end_date,
        )
        .select_related("leave")
        .order_by("date")
    )


def get_confirmed_leave_days_for_member_in_range(
    member: User,
    start_date: datetime.date,
    end_date: datetime.date,
) -> Decimal:
    entries = get_day_entries_for_member_in_range(member.id, start_date, end_date)
    total = Decimal("0")
    for entry in entries:
        total += Decimal("0.5") if entry.is_half_day else Decimal("1")
    return total
