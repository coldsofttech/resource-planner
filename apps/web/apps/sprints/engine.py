from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal


class SprintEngine:
    """Computed properties for a single sprint."""

    @staticmethod
    def days_remaining(end_date: date | None) -> int:
        if not end_date:
            return 0
        return (end_date - date.today()).days

    @staticmethod
    def compute_status(start_date: date, end_date: date) -> str:
        from apps.sprints.constants import SprintStatus

        today = date.today()
        if today < start_date:
            return SprintStatus.FUTURE
        if start_date <= today <= end_date:
            return SprintStatus.IN_PROGRESS
        return SprintStatus.EXPIRED


class SprintGenerationEngine:
    """Generates sprint date ranges for a financial year.

    Named 'Planner' because it is responsible for planning the full sprint
    schedule — computing non-overlapping windows, numbering, and naming each
    sprint — before handing the results to SprintService for persistence.
    The corresponding API endpoint is POST /api/v1/sprints/generate/.
    """

    @staticmethod
    def _get_config() -> tuple[str, int, int]:
        """Returns (name_prefix, start_number, duration_days)."""
        from apps.configurations.selectors import Sprint as SprintConfig

        try:
            prefix = SprintConfig.get_sprint_name_prefix()
        except Exception:
            prefix = "Sprint"
        try:
            start_number = SprintConfig.get_sprint_start_number()
        except Exception:
            start_number = 1
        try:
            duration_days = SprintConfig.get_sprint_duration_days()
        except Exception:
            duration_days = 14
        return prefix, start_number, duration_days

    @staticmethod
    def generate_date_windows(
        fy_start: date, fy_end: date, duration_days: int
    ) -> list[tuple[date, date]]:
        """Return (start, end) pairs that exactly tile fy_start..fy_end."""
        windows: list[tuple[date, date]] = []
        current = fy_start
        while current <= fy_end:
            window_end = min(current + timedelta(days=duration_days - 1), fy_end)
            windows.append((current, window_end))
            current = window_end + timedelta(days=1)
        return windows

    @classmethod
    def plan(
        cls,
        fy_start: date,
        fy_end: date,
        next_sprint_number: int,
    ) -> list[dict]:
        """Build a list of sprint dicts ready for bulk creation.

        Each dict contains: sprint_number, name, start_date, end_date, month, status.
        """
        prefix, _cfg_start, duration_days = cls._get_config()
        windows = cls.generate_date_windows(fy_start, fy_end, duration_days)

        planned: list[dict] = []
        for idx, (w_start, w_end) in enumerate(windows):
            number = next_sprint_number + idx
            planned.append(
                {
                    "sprint_number": number,
                    "name": f"{prefix} {number}",
                    "start_date": w_start,
                    "end_date": w_end,
                    "month": w_end.strftime("%Y-%m"),
                    "status": SprintEngine.compute_status(w_start, w_end),
                }
            )
        return planned


class SprintCapacityEngine:
    """Computes and persists per-member capacity for a sprint.

    Capacity = working_days - holiday_days - leave_days.

    All computation is driven by real DB data (holidays, leave day entries,
    and user profiles for location).  The engine performs one DB upsert per
    active user, so rebuild_for_sprint is O(n_users) in DB round-trips.
    """

    @staticmethod
    def compute_working_days(start_date: date, end_date: date) -> Decimal:
        """Count Mon–Fri days between start_date and end_date, inclusive."""
        total = (end_date - start_date).days + 1
        full_weeks, remaining = divmod(total, 7)
        weekdays = full_weeks * 5
        start_wd = start_date.weekday()  # 0=Mon … 6=Sun
        for i in range(remaining):
            if (start_wd + i) % 7 < 5:
                weekdays += 1
        return Decimal(weekdays)

    @staticmethod
    def compute_holiday_days(
        start_date: date, end_date: date, location_id: int | None
    ) -> Decimal:
        """Count holidays within the sprint window for a location.

        Weekday holidays only — weekend holidays are not counted since they
        have no impact on working capacity.
        """
        if not location_id:
            return Decimal(0)
        from apps.holidays.models import Holiday

        count = (
            Holiday.objects.filter(
                location_id=location_id,
                date__gte=start_date,
                date__lte=end_date,
            )
            .exclude(date__week_day__in=[1, 7])  # 1=Sunday, 7=Saturday
            .count()
        )
        return Decimal(count)

    @staticmethod
    def compute_leave_days(start_date: date, end_date: date, member_id: int) -> Decimal:
        """Sum approved leave day entries for a member within the sprint window.

        Uses LeaveDayEntry rows (one per working day), counting 0.5 for
        half-day entries and 1.0 for full-day entries.
        """
        from apps.leaves.models import LeaveDayEntry

        entries = LeaveDayEntry.objects.filter(
            leave__member_id=member_id,
            date__gte=start_date,
            date__lte=end_date,
        ).values_list("is_half_day", flat=True)

        total = sum(
            (Decimal("0.5") if half else Decimal("1") for half in entries), Decimal("0")
        )
        return total

    @classmethod
    def compute_for_member(
        cls,
        sprint: "Sprint",  # type: ignore[name-defined]  # noqa: F821
        member_id: int,
        location_id: int | None,
        joined_date: date | None = None,
        leaving_date: date | None = None,
    ) -> dict:
        eff_start = sprint.start_date
        eff_end = sprint.end_date

        if joined_date and joined_date > eff_start:
            eff_start = joined_date
        if leaving_date and leaving_date < eff_end:
            eff_end = leaving_date

        if eff_end < eff_start:
            return {
                "working_days": Decimal(0),
                "holiday_days": Decimal(0),
                "leave_days": Decimal(0),
                "net_capacity": Decimal(0),
            }

        working = cls.compute_working_days(eff_start, eff_end)
        holidays = cls.compute_holiday_days(eff_start, eff_end, location_id)
        leaves = cls.compute_leave_days(eff_start, eff_end, member_id)
        net = max(Decimal(0), working - holidays - leaves)
        return {
            "working_days": working,
            "holiday_days": holidays,
            "leave_days": leaves,
            "net_capacity": net,
        }

    @classmethod
    def rebuild_for_sprint(
        cls,
        sprint: "Sprint",  # type: ignore[name-defined]  # noqa: F821
        actor=None,
    ) -> int:
        """Upsert Capacity rows for every active user for the given sprint.

        Returns the total number of rows upserted.
        """
        from apps.sprints.models import Capacity
        from apps.users.models import User

        members = User.objects.filter(is_active=True).select_related(
            "profile", "profile__location"
        )

        count = 0
        for member in members:
            profile = getattr(member, "profile", None)
            location_id = getattr(profile, "location_id", None) if profile else None
            joined_date = getattr(profile, "joined_date", None) if profile else None
            leaving_date = getattr(profile, "leaving_date", None) if profile else None
            data = cls.compute_for_member(
                sprint, member.pk, location_id, joined_date, leaving_date
            )
            Capacity.objects.update_or_create(
                sprint=sprint,
                member=member,
                defaults={
                    **data,
                    "updated_by": actor,
                },
            )
            count += 1
        return count
