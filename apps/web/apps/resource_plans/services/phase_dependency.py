from __future__ import annotations

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.models import (
    Plan,
    PlanPhase,
    PlanPhaseDependency,
    PlanVersion,
    PlanVersionTeam,
)


class PlanPhaseDependencyService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "plan_phase_dependency"

    def _snapshot(self, obj: PlanPhaseDependency) -> dict:
        return {
            "phase_code": obj.phase.code,
            "predecessor_phase_code": obj.predecessor_phase.code,
            "dependency_type": obj.dependency_type,
            "lag_sprints": obj.lag_sprints,
        }

    def _resource_code(
        self, plan: Plan, version_number: int, dependency: PlanPhaseDependency
    ) -> str:
        return f"{plan.code}-v{version_number}-{dependency.code}"

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

    def _get_dependency(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
        dependency_version_code: str,
    ) -> PlanPhaseDependency:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        obj = selectors.get_dependency_by_code(dependency_version_code)
        if obj is None or obj.phase_id != phase.id:
            raise NotFoundException(
                resource="PlanPhaseDependency",
                lookup_field="code",
                lookup_value=dependency_version_code,
            )
        return obj

    def _resolve_predecessor(
        self, version: PlanVersion, phase: PlanPhase, predecessor_phase_code: str
    ) -> PlanPhase:
        predecessor = selectors.get_phase_by_code(predecessor_phase_code)
        if (
            predecessor is None
            or predecessor.plan_project_team.plan_project.version_id != version.id
        ):
            raise NotFoundException(
                resource="PlanPhase",
                lookup_field="code",
                lookup_value=predecessor_phase_code,
            )
        if predecessor.id == phase.id:
            raise ValidationException("A phase cannot depend on itself.")
        return predecessor

    def list_for_phase(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
    ) -> list[PlanPhaseDependency]:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return list(selectors.get_dependencies_for_phase(phase))

    def list_available_predecessors(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
    ) -> list[PlanPhase]:
        version_obj = self._get_version(plan_code, version)
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return list(selectors.get_available_predecessor_phases(version_obj, phase))

    @transaction.atomic
    def create(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
        predecessor_phase_code: str,
        dependency_type: str,
        lag_sprints: int,
    ) -> PlanPhaseDependency:
        version_obj = self._get_version(plan_code, version)
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        predecessor = self._resolve_predecessor(
            version_obj, phase, predecessor_phase_code
        )

        if selectors.dependency_exists(phase, predecessor):
            raise AlreadyExistsException(
                detail="This predecessor dependency already exists for this phase."
            )

        obj = PlanPhaseDependency.objects.create(
            phase=phase,
            predecessor_phase=predecessor,
            dependency_type=dependency_type,
            lag_sprints=lag_sprints,
            created_by=self.user,
            updated_by=self.user,
        )

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                phase.plan_project_team.plan_project.version.plan,
                phase.plan_project_team.plan_project.version.version,
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
        dependency_version_code: str,
        predecessor_phase_code: str,
        dependency_type: str,
        lag_sprints: int,
    ) -> PlanPhaseDependency:
        version_obj = self._get_version(plan_code, version)
        obj = self._get_dependency(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            dependency_version_code=dependency_version_code,
        )
        before = self._snapshot(obj)

        predecessor = self._resolve_predecessor(
            version_obj, obj.phase, predecessor_phase_code
        )

        if selectors.dependency_exists(obj.phase, predecessor, exclude_pk=obj.pk):
            raise AlreadyExistsException(
                detail="This predecessor dependency already exists for this phase."
            )

        obj.predecessor_phase = predecessor
        obj.dependency_type = dependency_type
        obj.lag_sprints = lag_sprints
        obj.updated_by = self.user
        obj.save(
            update_fields=[
                "predecessor_phase",
                "dependency_type",
                "lag_sprints",
                "updated_by",
                "updated_at",
            ]
        )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                obj.phase.plan_project_team.plan_project.version.plan,
                obj.phase.plan_project_team.plan_project.version.version,
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
        dependency_version_code: str,
    ) -> None:
        obj = self._get_dependency(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            dependency_version_code=dependency_version_code,
        )
        before = self._snapshot(obj)
        resource_code = self._resource_code(
            obj.phase.plan_project_team.plan_project.version.plan,
            obj.phase.plan_project_team.plan_project.version.version,
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
