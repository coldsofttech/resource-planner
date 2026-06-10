from __future__ import annotations

import datetime
from decimal import Decimal


class LeaveEngine:
    @staticmethod
    def get_working_dates(
        member_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[datetime.date]:
        """Return the list of working dates in [start_date, end_date], excluding
        weekends and public holidays at the member's location."""
        from apps.users.models import UserProfile

        location = None
        try:
            profile = UserProfile.objects.select_related("location").get(
                user_id=member_id
            )
            location = profile.location
        except UserProfile.DoesNotExist:
            pass

        holiday_dates: set[datetime.date] = set()
        if location is not None:
            from apps.holidays.models import Holiday

            qs = Holiday.objects.filter(
                location=location,
                date__gte=start_date,
                date__lte=end_date,
            ).values_list("date", flat=True)
            holiday_dates = set(qs)

        working: list[datetime.date] = []
        current = start_date
        while current <= end_date:
            if current.weekday() < 5 and current not in holiday_dates:
                working.append(current)
            current += datetime.timedelta(days=1)

        return working

    @staticmethod
    def calculate_days(
        member_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        is_half_day: bool,
    ) -> Decimal:
        """Return the number of working days for a leave, excluding weekends and
        public holidays at the member's location."""
        if is_half_day:
            return Decimal("0.5")

        dates = LeaveEngine.get_working_dates(member_id, start_date, end_date)
        return Decimal(str(len(dates)))

    @staticmethod
    def sync_day_entries(leave) -> None:
        """Delete and recreate LeaveDayEntry rows for *leave*.

        Callable from both the service layer (inside a transaction) and signal
        handlers (no user context). For a half-day leave the single date is
        recorded with is_half_day=True; for full-day leaves each working date
        gets an entry with is_half_day=False.
        """
        from apps.leaves.models import LeaveDayEntry

        LeaveDayEntry.objects.filter(leave=leave).delete()

        if leave.is_half_day:
            LeaveDayEntry.objects.create(
                leave=leave,
                date=leave.start_date,
                is_half_day=True,
            )
            return

        working_dates = LeaveEngine.get_working_dates(
            member_id=leave.member_id,
            start_date=leave.start_date,
            end_date=leave.end_date,
        )
        if working_dates:
            LeaveDayEntry.objects.bulk_create(
                [
                    LeaveDayEntry(leave=leave, date=d, is_half_day=False)
                    for d in working_dates
                ]
            )
