"""Extraction logic for the Weekly Wins standard report.

Kept separate from services.py so the report's data-shaping logic can grow
(new standard reports each get their own module here) without bloating the
reports app's service layer.
"""

from __future__ import annotations

from datetime import date as date_type

from apps.wins.models import Win, WinEntry

REPORT_SLUG = "weekly-wins"


def resolve_win(
    *, mode: str, date: date_type | None = None, win_code: str | None = None
) -> Win | None:
    """Resolve the single Win week the report should run for."""
    if mode == "week":
        if not win_code:
            return None
        return Win.objects.filter(code=win_code).first()
    if not date:
        return None
    return Win.objects.filter(start_date__lte=date, end_date__gte=date).first()


def get_entries(win: Win) -> list[WinEntry]:
    return list(
        WinEntry.objects.select_related("team")
        .filter(win=win)
        .order_by("team__name", "-created_at")
    )


def build_report_data(win: Win) -> dict:
    """Shape a resolved Win + its entries into the report's row structure."""
    week_label = f"Week {win.week_number}"
    date_range_label = win.date_range_label
    status_display = win.get_status_display()

    rows = [
        {
            "team": entry.team.name,
            "week": week_label,
            "date_range": date_range_label,
            "title": entry.title,
            "description": entry.description,
            "status": win.status,
            "status_display": status_display,
        }
        for entry in get_entries(win)
    ]

    return {
        "win": {
            "code": win.code,
            "week_number": win.week_number,
            "week": week_label,
            "date_range": date_range_label,
            "status": win.status,
            "status_display": status_display,
        },
        "entries": rows,
    }
