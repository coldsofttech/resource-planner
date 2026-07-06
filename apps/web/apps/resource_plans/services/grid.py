from __future__ import annotations

from decimal import Decimal

from apps.core.exceptions import NotFoundException
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.models import (
    AllocationSet,
    PlaceholderEngineer,
    Plan,
    PlanVersion,
)
from apps.sprints import selectors as sprint_selectors
from apps.sprints.models import Sprint
from apps.teams import selectors as team_selectors
from apps.teams.models import Team
from apps.users.models import User


class GridService(AuditableService):
    """Read-only data assembly for the Allocation Grid (#182) — one method per
    grid row (Capacity, Absences, Allocated Capacity, Allocations). Each
    endpoint's sprint axis is always the plan's full financial year (not just
    sprints with data), so the frontend can render a complete grid.
    """

    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "grid"

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

    def _resolve_teams_and_members(
        self, version: PlanVersion, team_code: str | None
    ) -> tuple[list[Team], dict[int, dict]]:
        if team_code:
            team = team_selectors.get_team_by_code(team_code)
            if team is None:
                raise NotFoundException(
                    resource="Team", lookup_field="code", lookup_value=team_code
                )
            teams = [team]
        else:
            teams = list(selectors.get_teams_for_version(version))

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
        """2dp string — DB-aggregated Decimals (e.g. SQLite Sum()) don't
        reliably preserve scale, so always quantize before returning."""
        return str(value.quantize(Decimal("0.01")))

    @staticmethod
    def _serialize_sprint(sprint: Sprint) -> dict:
        return {"sprint_code": sprint.code, "sprint_number": sprint.sprint_number}

    @classmethod
    def _serialize_sprints(cls, sprints: list[Sprint]) -> list[dict]:
        return [cls._serialize_sprint(s) for s in sprints]

    @staticmethod
    def _member_fields(member: User) -> dict:
        profile = getattr(member, "profile", None)
        display_name = (profile.display_name if profile else "") or member.email
        return {
            "member_code": profile.code if profile else None,
            "member_name": display_name,
        }

    @staticmethod
    def _placeholder_fields(placeholder: PlaceholderEngineer) -> dict:
        return {
            "member_code": placeholder.code,
            "member_name": placeholder.name,
        }

    @staticmethod
    def _team_codes_names(teams: list[Team]) -> dict:
        return {
            "team_codes": [t.code for t in teams],
            "team_names": [t.name for t in teams],
        }

    # ------------------------------------------------------------------ #
    # Row 1 — Capacity
    # ------------------------------------------------------------------ #

    def capacity(
        self, *, plan_code: str, version: int, team_code: str | None = None
    ) -> dict:
        version_obj = self._get_version(plan_code, version)
        _, members = self._resolve_teams_and_members(version_obj, team_code)
        sprints = self._sprint_axis(version_obj)

        rows = selectors.get_member_capacities_for_version(
            version_obj, member_ids=list(members.keys())
        )

        cells: dict[int, dict[int, Decimal]] = {}
        totals: dict[int, Decimal] = {}
        for mc in rows:
            cells.setdefault(mc.member_id, {})[mc.sprint_id] = mc.net_capacity
            totals[mc.sprint_id] = totals.get(mc.sprint_id, Decimal("0")) + (
                mc.net_capacity
            )

        return {
            "sprints": self._serialize_sprints(sprints),
            "totals": [
                {
                    **self._serialize_sprint(s),
                    "net_capacity": self._fmt(totals.get(s.id, Decimal("0"))),
                }
                for s in sprints
            ],
            "members": [
                {
                    **self._member_fields(info["member"]),
                    **self._team_codes_names(info["teams"]),
                    "cells": [
                        {
                            **self._serialize_sprint(s),
                            "net_capacity": self._fmt(
                                cells.get(member_id, {}).get(s.id, Decimal("0"))
                            ),
                        }
                        for s in sprints
                    ],
                }
                for member_id, info in members.items()
            ],
        }

    # ------------------------------------------------------------------ #
    # Row 2 — Absences
    # ------------------------------------------------------------------ #

    def absences(
        self, *, plan_code: str, version: int, team_code: str | None = None
    ) -> dict:
        version_obj = self._get_version(plan_code, version)
        _, members = self._resolve_teams_and_members(version_obj, team_code)
        sprints = self._sprint_axis(version_obj)

        rows = selectors.get_member_capacities_for_version(
            version_obj, member_ids=list(members.keys())
        )

        zero_bucket = {
            "holiday_days": Decimal("0"),
            "leave_days": Decimal("0"),
            "placeholder_leave_days": Decimal("0"),
        }
        per_member: dict[int, dict[int, dict[str, Decimal]]] = {}
        totals: dict[int, dict[str, Decimal]] = {}
        for mc in rows:
            member_bucket = per_member.setdefault(mc.member_id, {}).setdefault(
                mc.sprint_id, dict(zero_bucket)
            )
            member_bucket["holiday_days"] += mc.holiday_days
            member_bucket["leave_days"] += mc.leave_days
            member_bucket["placeholder_leave_days"] += mc.placeholder_leave_days

            team_bucket = totals.setdefault(mc.sprint_id, dict(zero_bucket))
            team_bucket["holiday_days"] += mc.holiday_days
            team_bucket["leave_days"] += mc.leave_days
            team_bucket["placeholder_leave_days"] += mc.placeholder_leave_days

        def _cell(bucket: dict[str, Decimal], sprint) -> dict:
            total_days = (
                bucket["holiday_days"]
                + bucket["leave_days"]
                + bucket["placeholder_leave_days"]
            )
            return {
                **self._serialize_sprint(sprint),
                "total_days": self._fmt(total_days),
                "holiday_days": self._fmt(bucket["holiday_days"]),
                "leave_days": self._fmt(bucket["leave_days"]),
                "placeholder_leave_days": self._fmt(bucket["placeholder_leave_days"]),
            }

        return {
            "sprints": self._serialize_sprints(sprints),
            "totals": [_cell(totals.get(s.id, zero_bucket), s) for s in sprints],
            "members": [
                {
                    **self._member_fields(info["member"]),
                    **self._team_codes_names(info["teams"]),
                    "cells": [
                        _cell(per_member.get(member_id, {}).get(s.id, zero_bucket), s)
                        for s in sprints
                    ],
                }
                for member_id, info in members.items()
            ],
        }

    # ------------------------------------------------------------------ #
    # Row 3 — Allocated Capacity
    # ------------------------------------------------------------------ #

    def allocated_capacity(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        team_code: str | None = None,
    ) -> dict:
        version_obj = self._get_version(plan_code, version)
        alloc_set = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        teams, members = self._resolve_teams_and_members(version_obj, team_code)
        team_id_filter = teams[0].id if team_code else None
        sprints = self._sprint_axis(version_obj)

        capacity_map = {
            (mc.member_id, mc.sprint_id): mc.net_capacity
            for mc in selectors.get_member_capacities_for_version(
                version_obj, member_ids=list(members.keys())
            )
        }
        allocated_map = {
            (row["member_id"], row["sprint_id"]): row["total_days"] or Decimal("0")
            for row in selectors.get_member_sprint_allocated_totals(
                alloc_set, team_id=team_id_filter
            )
            if row["member_id"] in members
        }

        return {
            "allocation_set_code": alloc_set.code,
            "sprints": self._serialize_sprints(sprints),
            "members": [
                {
                    **self._member_fields(info["member"]),
                    **self._team_codes_names(info["teams"]),
                    "cells": [
                        {
                            **self._serialize_sprint(s),
                            "allocated_days": self._fmt(
                                allocated_map.get((member_id, s.id), Decimal("0"))
                            ),
                            "net_capacity": self._fmt(
                                capacity_map.get((member_id, s.id), Decimal("0"))
                            ),
                        }
                        for s in sprints
                    ],
                }
                for member_id, info in members.items()
            ],
        }

    # ------------------------------------------------------------------ #
    # Row 4 — Allocations
    # ------------------------------------------------------------------ #

    def allocations(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        team_code: str | None = None,
    ) -> dict:
        version_obj = self._get_version(plan_code, version)
        alloc_set = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        team_id_filter = None
        if team_code:
            team = team_selectors.get_team_by_code(team_code)
            if team is None:
                raise NotFoundException(
                    resource="Team", lookup_field="code", lookup_value=team_code
                )
            team_id_filter = team.id

        sprints = self._sprint_axis(version_obj)
        version_projects = {
            vp.project_id: vp for vp in selectors.get_configured_projects(version_obj)
        }

        groups: dict[tuple, dict] = {}
        for alloc in selectors.get_allocations_for_set(
            alloc_set, team_id=team_id_filter
        ):
            assignee_key = (
                ("member", alloc.member_id)
                if alloc.member_id
                else ("placeholder", alloc.placeholder_engineer_id)
            )
            key = (assignee_key, alloc.team_id, alloc.project_id, alloc.phase_id)
            if key not in groups:
                vp = version_projects.get(alloc.project_id)
                assignee_fields = (
                    {"is_placeholder": False, **self._member_fields(alloc.member)}
                    if alloc.member_id
                    else {
                        "is_placeholder": True,
                        **self._placeholder_fields(alloc.placeholder_engineer),
                    }
                )
                groups[key] = {
                    **assignee_fields,
                    "team_code": alloc.team.code,
                    "team_name": alloc.team.name,
                    "programme_code": (
                        alloc.project.programme.code
                        if alloc.project.programme_id
                        else None
                    ),
                    "programme_name": (
                        alloc.project.programme.name
                        if alloc.project.programme_id
                        else None
                    ),
                    "project_code": alloc.project.code,
                    "project_name": alloc.project.name,
                    "phase_code": alloc.phase.code if alloc.phase_id else None,
                    "phase_name": alloc.phase.name if alloc.phase_id else None,
                    "priority": vp.effective_priority if vp else None,
                    "confidence": vp.effective_confidence if vp else None,
                    "_cells": {},
                }
            groups[key]["_cells"][alloc.sprint_id] = alloc

        results = []
        for group in groups.values():
            cells_map = group.pop("_cells")
            group["cells"] = [
                {
                    **self._serialize_sprint(s),
                    "allocation_code": (
                        cells_map[s.id].code if s.id in cells_map else None
                    ),
                    "days": self._fmt(
                        cells_map[s.id].effective_days
                        if s.id in cells_map
                        else Decimal("0")
                    ),
                }
                for s in sprints
            ]
            results.append(group)

        return {
            "allocation_set_code": alloc_set.code,
            "sprints": self._serialize_sprints(sprints),
            "results": results,
        }
