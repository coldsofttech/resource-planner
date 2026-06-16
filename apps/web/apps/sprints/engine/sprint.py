from __future__ import annotations

from datetime import date, timedelta


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
