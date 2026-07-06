"""Extraction logic for the Monthly Finance Report standard report.

Kept separate from services.py so the report's data-shaping logic can grow
without bloating the reports app's service layer (see kpi_estimate_accuracy.py).

For a selected financial year + month, resolves every sprint that falls in
that month and aggregates `ProjectSprintActual` rows into per-project
totals (days + cost). The report is only considered "complete" once every
sprint in the month has at least one recorded actual — otherwise the UI
shows a hint instead of the data table, since the totals would be partial.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.db.models import Sum

from apps.financial_years.models import FinancialYear
from apps.projects.models import ProjectSprintActual
from apps.sprints.models import Sprint

REPORT_SLUG = "monthly-finance-report"


def _month_label(month: str) -> str:
    return datetime.strptime(month, "%Y-%m").strftime("%b %Y")


def get_sprints_for_month(fy: FinancialYear, month: str) -> list[Sprint]:
    return list(
        Sprint.objects.filter(financial_year=fy, month=month).order_by("sprint_number")
    )


def _sprints_with_actuals(sprint_ids: list[int]) -> set[int]:
    return set(
        ProjectSprintActual.objects.filter(sprint_id__in=sprint_ids)
        .values_list("sprint_id", flat=True)
        .distinct()
    )


def build_report_data(fy: FinancialYear, month: str) -> dict:
    sprints = get_sprints_for_month(fy, month)
    sprint_ids = [s.id for s in sprints]
    sprints_with_actuals = _sprints_with_actuals(sprint_ids)

    sprint_rows = [
        {
            "code": sprint.code,
            "name": sprint.name,
            "status": sprint.status,
            "status_display": sprint.get_status_display(),
            "has_actuals": sprint.id in sprints_with_actuals,
        }
        for sprint in sprints
    ]

    is_complete = bool(sprints) and len(sprints_with_actuals) == len(sprint_ids)

    rows: list[dict] = []
    totals = {
        "project_count": 0,
        "total_days": str(Decimal("0")),
        "total_cost": str(Decimal("0")),
    }

    if is_complete:
        aggregates = (
            ProjectSprintActual.objects.filter(sprint_id__in=sprint_ids)
            .values(
                "project_code__value",
                "project__name",
                "project__programme__name",
            )
            .annotate(total_days=Sum("total_days"), total_cost=Sum("total_cost"))
            .order_by("project__name")
        )

        grand_days = Decimal("0")
        grand_cost = Decimal("0")
        for row in aggregates:
            total_days = row["total_days"] or Decimal("0")
            total_cost = row["total_cost"] or Decimal("0")
            grand_days += total_days
            grand_cost += total_cost
            rows.append(
                {
                    "project_code": row["project_code__value"] or "—",
                    "project": row["project__name"] or "—",
                    "programme": row["project__programme__name"] or "—",
                    "total_days": str(total_days),
                    "total_cost": str(total_cost),
                }
            )

        totals = {
            "project_count": len(rows),
            "total_days": str(grand_days),
            "total_cost": str(grand_cost),
        }

    return {
        "fy": {"code": fy.code, "name": fy.long_fy},
        "month": month,
        "month_label": _month_label(month),
        "sprints": sprint_rows,
        "is_complete": is_complete,
        "rows": rows,
        "totals": totals,
    }
