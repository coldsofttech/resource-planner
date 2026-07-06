"""Extraction logic for the Demand vs. Capacity standard report.

Kept separate from services.py so the report's data-shaping logic can grow
without bloating the reports app's service layer (see sprint_forecast_vs_actuals.py).

Demand is sourced from `resource_plans.Allocation` (the resource-plan engine's
per-sprint, per-member/placeholder output for a Plan Version's active
`AllocationSet`). Capacity — and the holiday/leave days lost within it — is
sourced from `resource_plans.MemberCapacity`, the plan-version-scoped capacity
snapshot taken by the same engine run, so demand and capacity are always
compared on a like-for-like snapshot rather than the live, ever-changing
`sprints.Capacity` table.

All monetary/day figures are converted to FTE using a flat 20 working days
per month, per #231.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.employment_types.models import EmploymentType
from apps.reports.models import DemandCapacityReportConfig
from apps.resource_plans import selectors as resource_plan_selectors
from apps.resource_plans.models import Allocation, AllocationSet, Plan, PlanVersion
from apps.sprints import selectors as sprint_selectors
from apps.teams import selectors as team_selectors
from apps.teams.models import Team
from apps.users.models import User

REPORT_SLUG = "demand-vs-capacity"

DAYS_PER_FTE_MONTH = Decimal("20")

UNMAPPED_CATEGORY = "Unmapped"
HOLIDAYS_LEAVES_ROW = "holidays_leaves"
TOTAL_DEMAND_ROW = "total_demand"
TOTAL_CAPACITY_ROW = "total_capacity"
FTE_RISK_ROW = "fte_risk"
UTILISATION_ROW = "utilisation"


def get_allocation_set(version: PlanVersion) -> AllocationSet | None:
    """The Active allocation set for the version, falling back to the most
    recently created one (e.g. a Draft-only version the engine hasn't
    activated yet) so the report still renders something meaningful."""
    active = resource_plan_selectors.get_active_allocation_set_for_version(version)
    if active is not None:
        return active
    return resource_plan_selectors.get_allocation_sets_for_version(version).first()


def _months_for_version(version: PlanVersion) -> list[str]:
    sprints = sorted(
        sprint_selectors.get_sprints_for_fy(version.plan.financial_year.code),
        key=lambda s: s.start_date,
    )
    months: list[str] = []
    seen: set[str] = set()
    for sprint in sprints:
        if sprint.month not in seen:
            seen.add(sprint.month)
            months.append(sprint.month)
    return months


def _month_label(month: str) -> str:
    return datetime.strptime(month, "%Y-%m").strftime("%b %Y")


def _fte(days: Decimal) -> str:
    return str((days / DAYS_PER_FTE_MONTH).quantize(Decimal("0.01")))


def _category_map(version: PlanVersion) -> dict[int, str]:
    rows = DemandCapacityReportConfig.objects.filter(plan_version=version).values(
        "programme_id", "category"
    )
    return {row["programme_id"]: row["category"] for row in rows}


def _resolve_member_ids(
    version: PlanVersion, team: Team | None, employment_type: EmploymentType | None
) -> list[int]:
    teams = (
        [team]
        if team is not None
        else list(resource_plan_selectors.get_teams_for_version(version))
    )
    member_ids: set[int] = set()
    for t in teams:
        member_ids.update(m.id for m in team_selectors.get_active_members_for_team(t))
    if employment_type is not None:
        member_ids = set(
            User.objects.filter(
                id__in=member_ids, profile__employment_type=employment_type
            ).values_list("id", flat=True)
        )
    return list(member_ids)


def _demand_by_category_month(
    allocation_set: AllocationSet,
    sprint_month_by_id: dict[int, str],
    category_map: dict[int, str],
    *,
    team: Team | None = None,
    employment_type: EmploymentType | None = None,
) -> dict[tuple[str, str], Decimal]:
    qs = Allocation.objects.filter(allocation_set=allocation_set)
    if team is not None:
        qs = qs.filter(team=team)
    if employment_type is not None:
        # Placeholder-engineer allocations have no member/profile and are
        # intentionally excluded once an employment-type filter is applied —
        # there is no employment type to attribute them to.
        qs = qs.filter(member__profile__employment_type=employment_type)

    rows = qs.values("project__programme_id", "sprint_id").annotate(
        days=Sum(Coalesce("override_days", "engine_days"))
    )

    totals: dict[tuple[str, str], Decimal] = {}
    for row in rows:
        month = sprint_month_by_id.get(row["sprint_id"])
        if month is None:
            continue
        category = category_map.get(row["project__programme_id"], UNMAPPED_CATEGORY)
        key = (category, month)
        totals[key] = totals.get(key, Decimal("0")) + (row["days"] or Decimal("0"))
    return totals


def _capacity_and_leave_by_month(
    version: PlanVersion,
    member_ids: list[int],
    sprint_month_by_id: dict[int, str],
) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    capacity_totals: dict[str, Decimal] = {}
    leave_totals: dict[str, Decimal] = {}
    for mc in resource_plan_selectors.get_member_capacities_for_version(
        version, member_ids=member_ids
    ):
        month = sprint_month_by_id.get(mc.sprint_id)
        if month is None:
            continue
        capacity_totals[month] = (
            capacity_totals.get(month, Decimal("0")) + mc.net_capacity
        )
        leave_totals[month] = leave_totals.get(month, Decimal("0")) + (
            mc.holiday_days + mc.leave_days
        )
    return capacity_totals, leave_totals


def _build_rows(
    months: list[str],
    categories: list[str],
    demand_totals: dict[tuple[str, str], Decimal],
    capacity_totals: dict[str, Decimal],
    leave_totals: dict[str, Decimal],
) -> list[dict]:
    rows: list[dict] = []
    total_demand_by_month = {m: Decimal("0") for m in months}

    for category in categories:
        values = {}
        for month in months:
            days = demand_totals.get((category, month), Decimal("0"))
            total_demand_by_month[month] += days
            values[month] = _fte(days)
        rows.append(
            {
                "key": f"category:{category}",
                "label": category,
                "type": "category",
                "values": values,
            }
        )

    rows.append(
        {
            "key": HOLIDAYS_LEAVES_ROW,
            "label": "Holidays/Leaves",
            "type": "info",
            "values": {m: _fte(leave_totals.get(m, Decimal("0"))) for m in months},
        }
    )
    rows.append(
        {
            "key": TOTAL_DEMAND_ROW,
            "label": "Total Demand",
            "type": "total",
            "values": {m: _fte(total_demand_by_month[m]) for m in months},
        }
    )
    rows.append(
        {
            "key": TOTAL_CAPACITY_ROW,
            "label": "Total Capacity",
            "type": "total",
            "values": {m: _fte(capacity_totals.get(m, Decimal("0"))) for m in months},
        }
    )

    fte_risk_values: dict[str, str] = {}
    utilisation_values: dict[str, str | None] = {}
    for month in months:
        capacity_days = capacity_totals.get(month, Decimal("0"))
        demand_days = total_demand_by_month[month]
        fte_risk_values[month] = _fte(capacity_days - demand_days)
        if capacity_days > 0:
            utilisation_values[month] = str(
                (demand_days / capacity_days * 100).quantize(Decimal("0.1"))
            )
        else:
            utilisation_values[month] = None
    rows.append(
        {
            "key": FTE_RISK_ROW,
            "label": "FTE Risk",
            "type": "risk",
            "values": fte_risk_values,
        }
    )
    rows.append(
        {
            "key": UTILISATION_ROW,
            "label": "Utilisation %",
            "type": "percent",
            "values": utilisation_values,
        }
    )
    return rows


def _scope_rows(
    version: PlanVersion,
    allocation_set: AllocationSet | None,
    months: list[str],
    sprint_month_by_id: dict[int, str],
    category_map: dict[int, str],
    categories: list[str],
    *,
    team: Team | None,
    employment_type: EmploymentType | None,
) -> list[dict]:
    demand_totals = (
        _demand_by_category_month(
            allocation_set,
            sprint_month_by_id,
            category_map,
            team=team,
            employment_type=employment_type,
        )
        if allocation_set is not None
        else {}
    )
    member_ids = _resolve_member_ids(version, team, employment_type)
    capacity_totals, leave_totals = _capacity_and_leave_by_month(
        version, member_ids, sprint_month_by_id
    )
    return _build_rows(months, categories, demand_totals, capacity_totals, leave_totals)


def _has_unmapped_demand(
    allocation_set: AllocationSet | None, category_map: dict[int, str]
) -> bool:
    if allocation_set is None:
        return False
    qs = Allocation.objects.filter(allocation_set=allocation_set)
    mapped_programme_ids = list(category_map.keys())
    if mapped_programme_ids:
        qs = qs.exclude(project__programme_id__in=mapped_programme_ids)
    return qs.exists()


def build_report_data(
    plan: Plan,
    version: PlanVersion,
    *,
    team: Team | None = None,
    employment_type: EmploymentType | None = None,
) -> dict:
    allocation_set = get_allocation_set(version)
    months = _months_for_version(version)
    sprints = sprint_selectors.get_sprints_for_fy(plan.financial_year.code)
    sprint_month_by_id = {s.id: s.month for s in sprints}
    category_map = _category_map(version)
    categories = sorted(set(category_map.values()))

    # Unmapped programmes (or allocations with no programme at all) still
    # carry demand — surface them as their own category rather than
    # silently dropping them from the totals.
    if _has_unmapped_demand(allocation_set, category_map):
        categories.append(UNMAPPED_CATEGORY)

    overall_rows = _scope_rows(
        version,
        allocation_set,
        months,
        sprint_month_by_id,
        category_map,
        categories,
        team=team,
        employment_type=employment_type,
    )

    teams_in_scope = (
        [team]
        if team is not None
        else list(resource_plan_selectors.get_teams_for_version(version))
    )
    team_blocks: list[dict] = []
    for t in teams_in_scope:
        team_blocks.append(
            {
                "team": {"code": t.code, "name": t.name},
                "rows": _scope_rows(
                    version,
                    allocation_set,
                    months,
                    sprint_month_by_id,
                    category_map,
                    categories,
                    team=t,
                    employment_type=employment_type,
                ),
            }
        )
    team_blocks.sort(key=lambda b: b["team"]["name"])

    return {
        "plan": {"code": plan.code, "name": plan.name},
        "version": {"number": version.version, "status": version.status},
        "team": {"code": team.code, "name": team.name} if team is not None else None,
        "employment_type": (
            {"code": employment_type.code, "name": employment_type.name}
            if employment_type is not None
            else None
        ),
        "has_allocation_set": allocation_set is not None,
        "months": months,
        "month_labels": {m: _month_label(m) for m in months},
        "categories": categories,
        "overall": {"rows": overall_rows},
        "teams": team_blocks,
    }
