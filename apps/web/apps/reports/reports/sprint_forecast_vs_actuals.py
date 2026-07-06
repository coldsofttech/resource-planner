"""Extraction logic for the Sprint Forecast vs. Actuals standard report.

Kept separate from services.py so the report's data-shaping logic can grow
without bloating the reports app's service layer (see weekly_wins.py).

Data is sourced from `RechargeDetail` — already-resolved per-sprint,
per-engineer/label/project/programme/finance-type rows populated when a
sprint's forecast or actuals review is marked complete (see
`RechargeDetailService.populate_from_sprint_forecast/actuals`).
"""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum

from apps.recharges.models import RechargeDetail
from apps.sprints.models import Sprint
from apps.teams.models import Team

REPORT_SLUG = "sprint-forecast-vs-actuals"

# Matches apps.recharges.constants.RechargeType values — plain strings here
# (rather than the enum) since RechargeDetail.type is filtered by value only.
_FORECAST = "forecast"
_ACTUAL = "actual"

GROUP_VIEWS = ("label", "project", "programme", "team", "engineer", "finance_type")

_GROUP_FIELDS = {
    "team": "team",
    "engineer": "engineer",
    "label": "label",
    "project": "project",
    "programme": "programme",
    "finance_type": "finance_type",
}


def _engineer_label(
    first_name: str | None, last_name: str | None, email: str | None
) -> str:
    name = f"{first_name or ''} {last_name or ''}".strip()
    return name or email or "Unassigned"


def _detail_totals(
    sprint: Sprint, team: Team | None, type_val: str
) -> dict[tuple, Decimal]:
    """Return {dimension_key_tuple: total_days} for one forecast/actual side,
    fully granular across all six dimensions at once."""
    qs = RechargeDetail.objects.filter(sprint=sprint, type=type_val)
    if team is not None:
        qs = qs.filter(team=team)

    rows = qs.values(
        "team__name",
        "assignee__user__first_name",
        "assignee__user__last_name",
        "assignee__user__email",
        "label__label",
        "project__name",
        "programme__name",
        "recharge_type__name",
    ).annotate(days=Sum("total_days"))

    totals: dict[tuple, Decimal] = {}
    for row in rows:
        key = (
            row["team__name"] or "No Team",
            _engineer_label(
                row["assignee__user__first_name"],
                row["assignee__user__last_name"],
                row["assignee__user__email"],
            ),
            row["label__label"] or "No Label",
            row["project__name"] or "No Project",
            row["programme__name"] or "No Programme",
            row["recharge_type__name"] or "Unmapped",
        )
        totals[key] = totals.get(key, Decimal("0")) + (row["days"] or Decimal("0"))
    return totals


def has_forecast_data(sprint: Sprint, team: Team | None = None) -> bool:
    qs = RechargeDetail.objects.filter(sprint=sprint, type=_FORECAST)
    if team is not None:
        qs = qs.filter(team=team)
    return qs.exists()


def has_actuals_data(sprint: Sprint, team: Team | None = None) -> bool:
    qs = RechargeDetail.objects.filter(sprint=sprint, type=_ACTUAL)
    if team is not None:
        qs = qs.filter(team=team)
    return qs.exists()


def build_all_rows(sprint: Sprint, team: Team | None = None) -> list[dict]:
    """Fully granular Team/Engineer/Label/Project/Programme/Finance Type rows,
    each with forecast_days, actual_days, and variance_days."""
    forecast_totals = _detail_totals(sprint, team, _FORECAST)
    actual_totals = _detail_totals(sprint, team, _ACTUAL)

    keys = set(forecast_totals) | set(actual_totals)
    rows = []
    for key in keys:
        team_name, engineer, label, project, programme, finance_type = key
        forecast_days = forecast_totals.get(key, Decimal("0"))
        actual_days = actual_totals.get(key, Decimal("0"))
        rows.append(
            {
                "team": team_name,
                "engineer": engineer,
                "label": label,
                "project": project,
                "programme": programme,
                "finance_type": finance_type,
                "forecast_days": str(forecast_days),
                "actual_days": str(actual_days),
                "variance_days": str(actual_days - forecast_days),
            }
        )
    rows.sort(key=lambda r: (r["team"], r["engineer"], r["label"]))
    return rows


def build_grouped_rows(all_rows: list[dict], view: str) -> list[dict]:
    """Reduce the fully granular rows down to totals for a single dimension."""
    field = _GROUP_FIELDS[view]
    totals: dict[str, dict[str, Decimal]] = {}
    for row in all_rows:
        key = row[field]
        bucket = totals.setdefault(
            key, {"forecast_days": Decimal("0"), "actual_days": Decimal("0")}
        )
        bucket["forecast_days"] += Decimal(row["forecast_days"])
        bucket["actual_days"] += Decimal(row["actual_days"])

    grouped = [
        {
            field: key,
            "forecast_days": str(bucket["forecast_days"]),
            "actual_days": str(bucket["actual_days"]),
            "variance_days": str(bucket["actual_days"] - bucket["forecast_days"]),
        }
        for key, bucket in totals.items()
    ]
    grouped.sort(key=lambda r: r[field])
    return grouped


def build_report_data(sprint: Sprint, team: Team | None = None) -> dict:
    all_rows = build_all_rows(sprint, team)

    total_forecast = sum((Decimal(r["forecast_days"]) for r in all_rows), Decimal("0"))
    total_actual = sum((Decimal(r["actual_days"]) for r in all_rows), Decimal("0"))

    return {
        "sprint": {
            "code": sprint.code,
            "name": sprint.name,
            "financial_year": sprint.financial_year.long_fy,
        },
        "team": {"code": team.code, "name": team.name} if team is not None else None,
        "has_forecast": has_forecast_data(sprint, team),
        "has_actuals": has_actuals_data(sprint, team),
        "totals": {
            "forecast_days": str(total_forecast),
            "actual_days": str(total_actual),
            "variance_days": str(total_actual - total_forecast),
        },
        "all_rows": all_rows,
        "grouped": {view: build_grouped_rows(all_rows, view) for view in GROUP_VIEWS},
    }
