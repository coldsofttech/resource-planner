from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.audit.services import AuditService
from apps.configurations.selectors import Sprint as SprintConfig
from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.constants import AllocationType
from apps.resource_plans.models import (
    Plan,
    PlanVersion,
    PlanVersionProject,
    PlanVersionTeam,
)
from apps.teams import selectors as team_selectors
from apps.teams.models import Team


class PlanVersionTeamService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "plan_version_team"

    def _snapshot(self, obj: PlanVersionTeam) -> dict:
        return {
            "plan_project_code": obj.plan_project.code,
            "team_code": obj.team.code,
            "allocation_type": obj.allocation_type,
            "allocation_percentage": (
                float(obj.allocation_percentage)
                if obj.allocation_percentage is not None
                else None
            ),
            "allocation_days": (
                float(obj.allocation_days) if obj.allocation_days is not None else None
            ),
            "allocation_budget": (
                float(obj.allocation_budget)
                if obj.allocation_budget is not None
                else None
            ),
            "allocated_days": float(obj.allocated_days),
            "sequence_order": obj.sequence_order,
        }

    def _resource_code(self, plan: Plan, version_number: int, team: Team) -> str:
        return f"{plan.code}-v{version_number}-{team.code}"

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

    def _get_plan_project(
        self, *, plan_code: str, version: int, project_version_code: str
    ) -> PlanVersionProject:
        version_obj = self._get_version(plan_code, version)
        obj = selectors.get_version_project_by_code(project_version_code)
        if obj is None or obj.version_id != version_obj.id:
            raise NotFoundException(
                resource="PlanVersionProject",
                lookup_field="code",
                lookup_value=project_version_code,
            )
        return obj

    def _get_version_team(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
    ) -> PlanVersionTeam:
        plan_project = self._get_plan_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )
        obj = selectors.get_version_team_by_code(team_version_code)
        if obj is None or obj.plan_project_id != plan_project.id:
            raise NotFoundException(
                resource="PlanVersionTeam",
                lookup_field="code",
                lookup_value=team_version_code,
            )
        return obj

    def _get_team(self, team_code: str) -> Team:
        team = team_selectors.get_team_by_code(team_code)
        if team is None:
            raise NotFoundException(
                resource="Team", lookup_field="code", lookup_value=team_code
            )
        return team

    def _resolve_allocation(
        self,
        plan_project: PlanVersionProject,
        allocation_type: str,
        value: Decimal,
    ) -> tuple[dict, Decimal]:
        if allocation_type == AllocationType.PERCENT:
            allocated_days = plan_project.days_required * value / Decimal("100")
            fields = {
                "allocation_percentage": value,
                "allocation_days": None,
                "allocation_budget": None,
            }
        elif allocation_type == AllocationType.DAYS:
            allocated_days = value
            fields = {
                "allocation_percentage": None,
                "allocation_days": value,
                "allocation_budget": None,
            }
        else:
            sprint_point_price = Decimal(str(SprintConfig.get_sprint_point_price()))
            allocated_days = (
                (value / sprint_point_price) if sprint_point_price else Decimal("0")
            )
            fields = {
                "allocation_percentage": None,
                "allocation_days": None,
                "allocation_budget": value,
            }
        return fields, allocated_days

    def list_for_project(
        self, *, plan_code: str, version: int, project_version_code: str
    ) -> list[PlanVersionTeam]:
        plan_project = self._get_plan_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )
        return list(selectors.get_teams_for_plan_project(plan_project))

    @transaction.atomic
    def create(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_code: str,
        allocation_type: str,
        value: Decimal,
        sequence_order: int = 1,
    ) -> PlanVersionTeam:
        plan_project = self._get_plan_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )
        team = self._get_team(team_code)

        if selectors.version_team_exists(plan_project, team):
            raise AlreadyExistsException(
                detail=f"Team {team_code} is already assigned to this project."
            )

        fields, allocated_days = self._resolve_allocation(
            plan_project, allocation_type, value
        )

        obj = PlanVersionTeam.objects.create(
            plan_project=plan_project,
            team=team,
            allocation_type=allocation_type,
            allocated_days=allocated_days,
            sequence_order=sequence_order,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        plan_project.recompute_flags()

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                plan_project.version.plan, plan_project.version.version, team
            ),
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        allocation_type: str,
        value: Decimal,
        sequence_order: int = 1,
    ) -> PlanVersionTeam:
        obj = self._get_version_team(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
        )
        before = self._snapshot(obj)

        fields, allocated_days = self._resolve_allocation(
            obj.plan_project, allocation_type, value
        )

        obj.allocation_type = allocation_type
        obj.allocation_percentage = fields["allocation_percentage"]
        obj.allocation_days = fields["allocation_days"]
        obj.allocation_budget = fields["allocation_budget"]
        obj.allocated_days = allocated_days
        obj.sequence_order = sequence_order
        obj.updated_by = self.user
        obj.save(
            update_fields=[
                "allocation_type",
                "allocation_percentage",
                "allocation_days",
                "allocation_budget",
                "allocated_days",
                "sequence_order",
                "updated_by",
                "updated_at",
            ]
        )
        obj.plan_project.recompute_flags()

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                obj.plan_project.version.plan,
                obj.plan_project.version.version,
                obj.team,
            ),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
    ) -> None:
        obj = self._get_version_team(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
        )
        before = self._snapshot(obj)
        resource_code = self._resource_code(
            obj.plan_project.version.plan, obj.plan_project.version.version, obj.team
        )
        # Captured before delete() — the FK reference would be gone afterward.
        plan_project = obj.plan_project
        obj.delete()
        plan_project.recompute_flags()

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=resource_code,
            before=before,
            actor=self.user,
        )
