from __future__ import annotations

from decimal import Decimal

from apps.core.exceptions import NotFoundException
from apps.core.services import AuditableService
from apps.employment_types import selectors as employment_type_selectors
from apps.projects import selectors as project_selectors
from apps.recharges import selectors as recharge_selectors
from apps.resource_plans import selectors
from apps.resource_plans.models import AllocationSet, Plan, PlanVersion
from apps.sprints import selectors as sprint_selectors
from apps.sprints.models import Sprint
from apps.teams import selectors as team_selectors
from apps.teams.models import Team
from apps.users.models import User


class UtilisationService(AuditableService):
    """Read-only aggregation for the Utilisation Graph (#196) — per-Team and
    per-Member rollups of net capacity, allocated days, and utilisation %
    across the plan's full financial year sprint axis."""

    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "utilisation"

    # ------------------------------------------------------------------ #
    # Shared lookups
    # ------------------------------------------------------------------ #

    def _get_plan(self, plan_code: str) -> Plan:
        obj = selectors.get_resource_plan_by_code(plan_code)
        if obj is None:
            raise NotFoundException(
                resource="Plan", lookup_field="code", lookup_value=plan_code
            )
        return obj

    def _get_version(self, plan_code: str, version: int) -> PlanVersion:
        plan = self._get_plan(plan_code)
        obj = selectors.get_version_by_number(plan, version)
        if obj is None:
            raise NotFoundException(
                resource="PlanVersion",
                lookup_field="version",
                lookup_value=version,
            )
        return obj

    def _get_allocation_set(
        self, *, plan_code: str, version: int, allocation_set_code: str
    ) -> AllocationSet:
        version_obj = self._get_version(plan_code, version)
        obj = selectors.get_allocation_set_by_code(allocation_set_code)
        if obj is None or obj.version_id != version_obj.id:
            raise NotFoundException(
                resource="AllocationSet",
                lookup_field="code",
                lookup_value=allocation_set_code,
            )
        return obj

    @staticmethod
    def _sprint_axis(version: PlanVersion) -> list[Sprint]:
        fy = version.plan.financial_year
        return list(sprint_selectors.get_sprints_for_fy(fy.code))

    def _resolve_teams(self, version: PlanVersion, team_code: str | None) -> list[Team]:
        if team_code:
            team = team_selectors.get_team_by_code(team_code)
            if team is None:
                raise NotFoundException(
                    resource="Team", lookup_field="code", lookup_value=team_code
                )
            return [team]
        return list(selectors.get_teams_for_version(version))

    def _resolve_teams_and_members(
        self, version: PlanVersion, team_code: str | None
    ) -> tuple[list[Team], dict[int, dict]]:
        teams = self._resolve_teams(version, team_code)
        members: dict[int, dict] = {}
        for team in teams:
            for member in team_selectors.get_active_members_for_team(team):
                entry = members.setdefault(member.id, {"member": member, "teams": []})
                entry["teams"].append(team)
        return teams, members

    # ------------------------------------------------------------------ #
    # Serialization helpers — flat, JSON-safe primitives only
    # ------------------------------------------------------------------ #

    @staticmethod
    def _fmt(value: Decimal) -> str:
        """2dp string — DB-aggregated Decimals don't reliably preserve
        scale, so always quantize before returning."""
        return str(value.quantize(Decimal("0.01")))

    @staticmethod
    def _fmt_pct(value: Decimal | None) -> str | None:
        return None if value is None else str(value.quantize(Decimal("0.1")))

    @staticmethod
    def _serialize_sprint(sprint: Sprint) -> dict:
        return {"sprint_code": sprint.code, "sprint_number": sprint.sprint_number}

    @classmethod
    def _serialize_sprints(cls, sprints: list[Sprint]) -> list[dict]:
        return [cls._serialize_sprint(s) for s in sprints]

    @staticmethod
    def _util_pct(allocated: Decimal, net_capacity: Decimal) -> Decimal | None:
        if net_capacity <= 0:
            return None
        return (allocated / net_capacity) * Decimal("100")

    @classmethod
    def _cells_and_summary(
        cls,
        sprints: list[Sprint],
        capacity: dict[int, Decimal],
        allocated: dict[int, Decimal],
    ) -> tuple[list[dict], dict]:
        cells = []
        total_net_capacity = Decimal("0")
        total_allocated = Decimal("0")
        util_values: list[Decimal] = []
        sprints_over = 0
        for s in sprints:
            net_cap = capacity.get(s.id, Decimal("0"))
            alloc = allocated.get(s.id, Decimal("0"))
            util_pct = cls._util_pct(alloc, net_cap)
            total_net_capacity += net_cap
            total_allocated += alloc
            if util_pct is not None:
                util_values.append(util_pct)
                if util_pct > 100:
                    sprints_over += 1
            cells.append(
                {
                    **cls._serialize_sprint(s),
                    "net_capacity": cls._fmt(net_cap),
                    "allocated_days": cls._fmt(alloc),
                    "util_pct": cls._fmt_pct(util_pct),
                }
            )
        avg_util_pct = (
            sum(util_values, Decimal("0")) / len(util_values)
            if util_values
            else Decimal("0")
        )
        summary = {
            "total_net_capacity": cls._fmt(total_net_capacity),
            "total_allocated": cls._fmt(total_allocated),
            "avg_util_pct": cls._fmt_pct(avg_util_pct),
            "sprints_over": sprints_over,
        }
        return cells, summary

    # ------------------------------------------------------------------ #
    # Teams tab
    # ------------------------------------------------------------------ #

    def teams(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        team_code: str | None = None,
        include_placeholders: bool = False,
    ) -> dict:
        version_obj = self._get_version(plan_code, version)
        alloc_set = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        teams = self._resolve_teams(version_obj, team_code)
        sprints = self._sprint_axis(version_obj)

        team_rows = []
        chart_capacity: dict[int, Decimal] = {}
        chart_allocated: dict[int, Decimal] = {}

        for team in teams:
            # Each team's own exclusive member set — avoids double-counting
            # net capacity for a member who belongs to more than one team.
            member_ids = [
                m.id for m in team_selectors.get_active_members_for_team(team)
            ]

            capacity: dict[int, Decimal] = {}
            for mc in selectors.get_member_capacities_for_version(
                version_obj, member_ids=member_ids
            ):
                capacity[mc.sprint_id] = (
                    capacity.get(mc.sprint_id, Decimal("0")) + mc.net_capacity
                )

            allocated: dict[int, Decimal] = {}
            for row in selectors.get_member_sprint_allocated_totals(
                alloc_set, team_id=team.id
            ):
                allocated[row["sprint_id"]] = allocated.get(
                    row["sprint_id"], Decimal("0")
                ) + (row["total_days"] or Decimal("0"))
            if include_placeholders:
                for row in selectors.get_team_placeholder_sprint_totals(
                    alloc_set, team_id=team.id
                ):
                    allocated[row["sprint_id"]] = allocated.get(
                        row["sprint_id"], Decimal("0")
                    ) + (row["total_days"] or Decimal("0"))

            for sprint_id, value in capacity.items():
                chart_capacity[sprint_id] = (
                    chart_capacity.get(sprint_id, Decimal("0")) + value
                )
            for sprint_id, value in allocated.items():
                chart_allocated[sprint_id] = (
                    chart_allocated.get(sprint_id, Decimal("0")) + value
                )

            cells, summary = self._cells_and_summary(sprints, capacity, allocated)
            team_rows.append(
                {
                    "team_code": team.code,
                    "team_name": team.name,
                    "cells": cells,
                    **summary,
                }
            )

        chart_cells, _ = self._cells_and_summary(
            sprints, chart_capacity, chart_allocated
        )

        return {
            "sprints": self._serialize_sprints(sprints),
            "chart_cells": chart_cells,
            "teams": team_rows,
        }

    # ------------------------------------------------------------------ #
    # Members tab
    # ------------------------------------------------------------------ #

    def members(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        team_code: str | None = None,
        member_code: str | None = None,
        employment_type_code: str | None = None,
        project_code: str | None = None,
    ) -> dict:
        version_obj = self._get_version(plan_code, version)
        alloc_set = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        _, members = self._resolve_teams_and_members(version_obj, team_code)
        sprints = self._sprint_axis(version_obj)

        if member_code:
            members = {
                mid: info
                for mid, info in members.items()
                if getattr(info["member"], "profile", None)
                and info["member"].profile.code == member_code
            }

        if employment_type_code:
            employment_type = employment_type_selectors.get_employment_type_by_code(
                employment_type_code
            )
            if employment_type is None:
                raise NotFoundException(
                    resource="EmploymentType",
                    lookup_field="code",
                    lookup_value=employment_type_code,
                )
            members = {
                mid: info
                for mid, info in members.items()
                if getattr(info["member"], "profile", None)
                and info["member"].profile.employment_type_id == employment_type.id
            }

        project_id = None
        if project_code:
            project = project_selectors.get_project_by_code(project_code)
            if project is None:
                raise NotFoundException(
                    resource="Project", lookup_field="code", lookup_value=project_code
                )
            project_id = project.id

        capacity_map: dict[tuple[int, int], Decimal] = {
            (mc.member_id, mc.sprint_id): mc.net_capacity
            for mc in selectors.get_member_capacities_for_version(
                version_obj, member_ids=list(members.keys())
            )
        }
        allocated_map: dict[tuple[int, int], Decimal] = {
            (row["member_id"], row["sprint_id"]): row["total_days"] or Decimal("0")
            for row in selectors.get_member_sprint_allocated_totals(
                alloc_set, project_id=project_id
            )
            if row["member_id"] in members
        }

        chart_capacity: dict[int, Decimal] = {}
        chart_allocated: dict[int, Decimal] = {}
        member_rows = []

        for member_id, info in members.items():
            capacity = {
                s.id: capacity_map.get((member_id, s.id), Decimal("0")) for s in sprints
            }
            allocated = {
                s.id: allocated_map.get((member_id, s.id), Decimal("0"))
                for s in sprints
            }
            for s in sprints:
                chart_capacity[s.id] = (
                    chart_capacity.get(s.id, Decimal("0")) + capacity[s.id]
                )
                chart_allocated[s.id] = (
                    chart_allocated.get(s.id, Decimal("0")) + allocated[s.id]
                )

            cells, summary = self._cells_and_summary(sprints, capacity, allocated)
            member: User = info["member"]
            profile = getattr(member, "profile", None)
            member_rows.append(
                {
                    "member_code": profile.code if profile else None,
                    "member_name": (profile.display_name if profile else "")
                    or member.email,
                    "team_names": [t.name for t in info["teams"]],
                    "cells": cells,
                    **summary,
                }
            )

        chart_cells, _ = self._cells_and_summary(
            sprints, chart_capacity, chart_allocated
        )

        return {
            "sprints": self._serialize_sprints(sprints),
            "chart_cells": chart_cells,
            "members": member_rows,
        }

    # ------------------------------------------------------------------ #
    # Programmes tab (#204)
    # ------------------------------------------------------------------ #

    def programmes(
        self,
        *,
        plan_code: str,
        version: int,
        programme_code: str | None = None,
    ) -> dict:
        """Per-programme Budget Baseline / Forecast Cost / Cumulative £
        rollup, scoped to the projects configured on this plan version.

        Budget Baseline sums PlanVersionProject.basis_amount (a currency
        figure regardless of its `basis` source — Budget/Estimate/Custom)
        across a programme's configured projects. Forecast Cost reads the
        existing Recharge rows (type=forecast), which are already populated
        by RechargeDetailService from imported sprint effort data — no new
        rate-card computation is introduced here. Cumulative is a running
        sum of Forecast Cost across the sprint axis.
        """
        version_obj = self._get_version(plan_code, version)
        sprints = self._sprint_axis(version_obj)

        configured = list(selectors.get_configured_projects(version_obj))

        programmes_map: dict[int, dict] = {}
        for pvp in configured:
            programme = pvp.project.programme
            if programme is None:
                continue
            entry = programmes_map.setdefault(
                programme.id,
                {
                    "programme": programme,
                    "project_ids": [],
                    "budget_baseline": Decimal("0"),
                },
            )
            entry["project_ids"].append(pvp.project_id)
            entry["budget_baseline"] += pvp.basis_amount

        if programme_code:
            programme = project_selectors.get_programme_by_code(programme_code)
            if programme is None or programme.id not in programmes_map:
                raise NotFoundException(
                    resource="Programme",
                    lookup_field="code",
                    lookup_value=programme_code,
                )
            programmes_map = {programme.id: programmes_map[programme.id]}

        programme_rows = []
        for entry in programmes_map.values():
            programme = entry["programme"]
            budget_baseline = entry["budget_baseline"]
            forecast_by_sprint = {
                row["sprint_id"]: row["total_cost"] or Decimal("0")
                for row in recharge_selectors.get_project_forecast_cost_by_sprint(
                    entry["project_ids"]
                )
            }

            cells = []
            cumulative = Decimal("0")
            total_forecast = Decimal("0")
            for s in sprints:
                forecast_cost = forecast_by_sprint.get(s.id, Decimal("0"))
                cumulative += forecast_cost
                total_forecast += forecast_cost
                cells.append(
                    {
                        **self._serialize_sprint(s),
                        "forecast_cost": self._fmt(forecast_cost),
                        "cumulative_cost": self._fmt(cumulative),
                        "budget_baseline": self._fmt(budget_baseline),
                    }
                )

            programme_rows.append(
                {
                    "programme_code": programme.code,
                    "programme_name": programme.name,
                    "cells": cells,
                    "total_budget": self._fmt(budget_baseline),
                    "total_forecast": self._fmt(total_forecast),
                }
            )

        programme_rows.sort(key=lambda r: r["programme_name"])

        return {
            "sprints": self._serialize_sprints(sprints),
            "programmes": programme_rows,
        }
