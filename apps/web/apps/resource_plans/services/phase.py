from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.models import Plan, PlanPhase, PlanVersion, PlanVersionTeam
from apps.sprints import selectors as sprint_selectors
from apps.sprints.models import Sprint


class PlanPhaseService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "plan_phase"

    def _snapshot(self, obj: PlanPhase) -> dict:
        return {
            "plan_project_team_code": obj.plan_project_team.code,
            "name": obj.name,
            "sequence_order": obj.sequence_order,
            "start_sprint_code": obj.start_sprint.code if obj.start_sprint_id else None,
            "end_sprint_code": obj.end_sprint.code if obj.end_sprint_id else None,
            "max_days_per_sprint": (
                float(obj.max_days_per_sprint)
                if obj.max_days_per_sprint is not None
                else None
            ),
            "ramp_pattern": obj.ramp_pattern,
            "allow_multiple_engineers": obj.allow_multiple_engineers,
            "split_mode": obj.split_mode,
            "notes": obj.notes,
            "days_effort": float(obj.days_effort),
        }

    def _resource_code(self, plan: Plan, version_number: int, phase: PlanPhase) -> str:
        return f"{plan.code}-v{version_number}-{phase.code}"

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

    def _get_plan_project_team(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
    ) -> PlanVersionTeam:
        version_obj = self._get_version(plan_code, version)
        plan_project = selectors.get_version_project_by_code(project_version_code)
        if plan_project is None or plan_project.version_id != version_obj.id:
            raise NotFoundException(
                resource="PlanVersionProject",
                lookup_field="code",
                lookup_value=project_version_code,
            )
        plan_project_team = selectors.get_version_team_by_code(team_version_code)
        if (
            plan_project_team is None
            or plan_project_team.plan_project_id != plan_project.id
        ):
            raise NotFoundException(
                resource="PlanVersionTeam",
                lookup_field="code",
                lookup_value=team_version_code,
            )
        return plan_project_team

    def _get_phase(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
    ) -> PlanPhase:
        plan_project_team = self._get_plan_project_team(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
        )
        obj = selectors.get_phase_by_code(phase_version_code)
        if obj is None or obj.plan_project_team_id != plan_project_team.id:
            raise NotFoundException(
                resource="PlanPhase",
                lookup_field="code",
                lookup_value=phase_version_code,
            )
        return obj

    def _resolve_sprint(self, sprint_code: str | None) -> Sprint | None:
        if not sprint_code:
            return None
        sprint = sprint_selectors.get_sprint_by_code(sprint_code)
        if sprint is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=sprint_code
            )
        return sprint

    def _validate_sprint_range(self, start: Sprint | None, end: Sprint | None) -> None:
        if start is None or end is None:
            return
        if start.sprint_number > end.sprint_number:
            raise ValidationException("Start sprint must not be after the end sprint.")

    def list_for_team(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
    ) -> list[PlanPhase]:
        plan_project_team = self._get_plan_project_team(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
        )
        return list(selectors.get_phases_for_plan_project_team(plan_project_team))

    @transaction.atomic
    def create(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        name: str,
        sequence_order: int,
        start_sprint_code: str | None = None,
        end_sprint_code: str | None = None,
        max_days_per_sprint: Decimal | None = None,
        ramp_pattern: str,
        allow_multiple_engineers: bool,
        split_mode: str,
        notes: str,
    ) -> PlanPhase:
        plan_project_team = self._get_plan_project_team(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
        )

        if selectors.phase_name_exists(plan_project_team, name):
            raise AlreadyExistsException(
                detail=f'A phase named "{name}" already exists for this team.'
            )

        start_sprint = self._resolve_sprint(start_sprint_code)
        end_sprint = self._resolve_sprint(end_sprint_code)
        self._validate_sprint_range(start_sprint, end_sprint)

        obj = PlanPhase.objects.create(
            plan_project_team=plan_project_team,
            name=name,
            sequence_order=sequence_order,
            start_sprint=start_sprint,
            end_sprint=end_sprint,
            max_days_per_sprint=max_days_per_sprint,
            ramp_pattern=ramp_pattern,
            allow_multiple_engineers=allow_multiple_engineers,
            split_mode=split_mode,
            notes=notes,
            days_effort=Decimal("0"),
            created_by=self.user,
            updated_by=self.user,
        )

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                plan_project_team.plan_project.version.plan,
                plan_project_team.plan_project.version.version,
                obj,
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
        phase_version_code: str,
        name: str,
        sequence_order: int,
        start_sprint_code: str | None = None,
        end_sprint_code: str | None = None,
        max_days_per_sprint: Decimal | None = None,
        ramp_pattern: str,
        allow_multiple_engineers: bool,
        split_mode: str,
        notes: str,
    ) -> PlanPhase:
        obj = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        before = self._snapshot(obj)

        if selectors.phase_name_exists(obj.plan_project_team, name, exclude_pk=obj.pk):
            raise AlreadyExistsException(
                detail=f'A phase named "{name}" already exists for this team.'
            )

        start_sprint = self._resolve_sprint(start_sprint_code)
        end_sprint = self._resolve_sprint(end_sprint_code)
        self._validate_sprint_range(start_sprint, end_sprint)

        obj.name = name
        obj.sequence_order = sequence_order
        obj.start_sprint = start_sprint
        obj.end_sprint = end_sprint
        obj.max_days_per_sprint = max_days_per_sprint
        obj.ramp_pattern = ramp_pattern
        obj.allow_multiple_engineers = allow_multiple_engineers
        obj.split_mode = split_mode
        obj.notes = notes
        obj.updated_by = self.user
        obj.save(
            update_fields=[
                "name",
                "sequence_order",
                "start_sprint",
                "end_sprint",
                "max_days_per_sprint",
                "ramp_pattern",
                "allow_multiple_engineers",
                "split_mode",
                "notes",
                "updated_by",
                "updated_at",
            ]
        )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                obj.plan_project_team.plan_project.version.plan,
                obj.plan_project_team.plan_project.version.version,
                obj,
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
        phase_version_code: str,
    ) -> None:
        obj = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        before = self._snapshot(obj)
        resource_code = self._resource_code(
            obj.plan_project_team.plan_project.version.plan,
            obj.plan_project_team.plan_project.version.version,
            obj,
        )
        obj.delete()

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=resource_code,
            before=before,
            actor=self.user,
        )
