"""Extraction logic for the Monthly Wins standard report.

Kept separate from services.py — see weekly_wins.py for the same convention.
"""

from __future__ import annotations

from collections import defaultdict

from apps.wins.constants import SurveyPhase, WinCategory
from apps.wins.models import (
    MonthlyWin,
    MonthlyWinResult,
    MonthlyWinSurveyNomination,
    WinEntry,
)

REPORT_SLUG = "monthly-wins"


def resolve_monthly_win(*, code: str | None) -> MonthlyWin | None:
    if not code:
        return None
    return MonthlyWin.objects.filter(code=code).first()


def _category_display(category: str) -> str:
    return dict(WinCategory.choices).get(category, category)


def build_phase1_rows(mw: MonthlyWin) -> list[dict]:
    """One row per (entry, category) nominated during Phase 1, with the
    number of Phase 1 votes it received."""
    status_display = mw.get_status_display()

    nominations = MonthlyWinSurveyNomination.objects.filter(
        survey__monthly_win=mw,
        survey__phase=SurveyPhase.PHASE_1,
        is_dismissed=False,
    ).select_related("entry__team", "entry__win")

    vote_counts: dict[tuple[int, str], int] = defaultdict(int)
    entries_by_key: dict[tuple[int, str], WinEntry] = {}
    for nomination in nominations:
        key = (nomination.entry_id, nomination.category)
        vote_counts[key] += 1
        entries_by_key[key] = nomination.entry

    rows = []
    for (entry_id, category), vote_count in vote_counts.items():
        entry = entries_by_key[(entry_id, category)]
        win = entry.win
        rows.append(
            {
                "label": f"Week {win.week_number}: {entry.title}",
                "phase1_votes": vote_count,
                "status": mw.status,
                "status_display": status_display,
                "team": entry.team.name,
                "week": f"Week {win.week_number}",
                "date_range": win.date_range_label,
                "win": f"{entry.title}: {entry.description}",
                "category": category,
                "category_display": _category_display(category),
            }
        )

    rows.sort(key=lambda r: (r["team"], r["week"], r["label"]))
    return rows


def build_phase2_data(mw: MonthlyWin) -> dict[str, dict]:
    """Declared Phase 2 results grouped by category, ranked."""
    results = (
        MonthlyWinResult.objects.filter(monthly_win=mw)
        .select_related("entry__team")
        .order_by("category", "rank")
    )

    grouped: dict[str, list[dict]] = {
        category: [] for category, _ in WinCategory.choices
    }
    for result in results:
        grouped[result.category].append(
            {
                "team": result.entry.team.name,
                "title": result.entry.title,
                "description": result.entry.description,
                "rank": result.rank,
                "vote_count": result.vote_count,
            }
        )

    return {
        category: {"label": label, "entries": grouped[category]}
        for category, label in WinCategory.choices
    }


def build_report_data(mw: MonthlyWin) -> dict:
    return {
        "monthly_win": {
            "code": mw.code,
            "name": mw.name,
            "status": mw.status,
            "status_display": mw.get_status_display(),
        },
        "phase1": build_phase1_rows(mw),
        "phase2": build_phase2_data(mw),
    }
