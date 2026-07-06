from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.models import (
    Plan,
    PlanPhase,
    PlanPhaseSegment,
    PlanVersion,
    PlanVersionTeam,
)


class PlanPhaseSegmentService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "plan_phase_segment"

    def _snapshot(self, obj: PlanPhaseSegment) -> dict:
        return {
            "phase_code": obj.phase.code,
            "segment_order": obj.segment_order,
            "segment_type": obj.segment_type,
            "start_percentage": float(obj.start_percentage),
            "end_percentage": float(obj.end_percentage),
            "progression": obj.progression,
            "duration": obj.duration,
            "step_count": obj.step_count,
        }

    def _resource_code(
        self, plan: Plan, version_number: int, segment: PlanPhaseSegment
    ) -> str:
        return f"{plan.code}-v{version_number}-{segment.code}"

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

    def _get_segment(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
        segment_version_code: str,
    ) -> PlanPhaseSegment:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        obj = selectors.get_segment_by_code(segment_version_code)
        if obj is None or obj.phase_id != phase.id:
            raise NotFoundException(
                resource="PlanPhaseSegment",
                lookup_field="code",
                lookup_value=segment_version_code,
            )
        return obj

    def list_for_phase(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
    ) -> list[PlanPhaseSegment]:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return list(selectors.get_segments_for_phase(phase))

    @transaction.atomic
    def create(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
        segment_type: str,
        start_percentage: Decimal,
        end_percentage: Decimal,
        progression: str,
        duration: int,
        step_count: int | None,
    ) -> PlanPhaseSegment:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )

        obj = PlanPhaseSegment.objects.create(
            phase=phase,
            segment_order=selectors.get_next_segment_order(phase),
            segment_type=segment_type,
            start_percentage=start_percentage,
            end_percentage=end_percentage,
            progression=progression,
            duration=duration,
            step_count=step_count,
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
    def delete(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
        segment_version_code: str,
    ) -> None:
        obj = self._get_segment(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            segment_version_code=segment_version_code,
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
