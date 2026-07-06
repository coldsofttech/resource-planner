from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.constants import AssignmentType
from apps.resource_plans.models import (
    Plan,
    PlanAssignment,
    PlanPhase,
    PlanVersion,
    PlanVersionTeam,
)
from apps.users import selectors as user_selectors
from apps.users.models import User


class PlanAssignmentService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "plan_assignment"

    def _snapshot(self, obj: PlanAssignment) -> dict:
        return {
            "phase_code": obj.phase.code,
            "member_code": obj.member.profile.code,
            "auto_assign": obj.auto_assign,
            "assignment_type": obj.assignment_type,
            "replaces_member_code": (
                obj.replaces_member.profile.code if obj.replaces_member_id else None
            ),
            "interim_sprint_count": obj.interim_sprint_count,
            "split_value": (
                float(obj.split_value) if obj.split_value is not None else None
            ),
            "includes_in_budget": obj.includes_in_budget,
            "notes": obj.notes,
        }

    def _resource_code(
        self, plan: Plan, version_number: int, assignment: PlanAssignment
    ) -> str:
        return f"{plan.code}-v{version_number}-{assignment.code}"

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

    def _get_assignment(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
        assignment_version_code: str,
    ) -> PlanAssignment:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        obj = selectors.get_assignment_by_code(assignment_version_code)
        if obj is None or obj.phase_id != phase.id:
            raise NotFoundException(
                resource="PlanAssignment",
                lookup_field="code",
                lookup_value=assignment_version_code,
            )
        return obj

    def _resolve_member(self, member_code: str) -> User:
        profile = user_selectors.get_member_by_code(member_code)
        if profile is None:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=member_code
            )
        return profile.user

    def _resolve_interim(
        self,
        assignment_type: str,
        replaces_member_code: str | None,
        interim_sprint_count: int | None,
        member: User,
    ) -> dict[str, User | int | None]:
        if assignment_type != AssignmentType.INTERIM:
            return {"replaces_member": None, "interim_sprint_count": None}

        if not replaces_member_code:
            raise ValidationException("A member to replace must be selected.")

        replaces_member = self._resolve_member(replaces_member_code)
        if replaces_member.id == member.id:
            raise ValidationException("A member cannot replace themselves.")
        return {
            "replaces_member": replaces_member,
            "interim_sprint_count": interim_sprint_count,
        }

    def _includes_in_budget(self, assignment_type: str) -> bool:
        return assignment_type == AssignmentType.ENGINEER

    def list_for_phase(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
    ) -> list[PlanAssignment]:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return list(selectors.get_assignments_for_phase(phase))

    @transaction.atomic
    def create(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
        member_code: str,
        auto_assign: bool,
        assignment_type: str,
        replaces_member_code: str | None,
        interim_sprint_count: int | None,
        split_value: Decimal | None,
        notes: str,
    ) -> PlanAssignment:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        member = self._resolve_member(member_code)
        interim_fields = self._resolve_interim(
            assignment_type, replaces_member_code, interim_sprint_count, member
        )

        obj = PlanAssignment.objects.create(
            phase=phase,
            member=member,
            auto_assign=auto_assign,
            assignment_type=assignment_type,
            split_value=split_value,
            includes_in_budget=self._includes_in_budget(assignment_type),
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
            **interim_fields,
        )
        phase.recompute_is_split_incomplete()

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
        assignment_version_code: str,
        member_code: str,
        auto_assign: bool,
        assignment_type: str,
        replaces_member_code: str | None,
        interim_sprint_count: int | None,
        split_value: Decimal | None,
        notes: str,
    ) -> PlanAssignment:
        obj = self._get_assignment(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            assignment_version_code=assignment_version_code,
        )
        before = self._snapshot(obj)

        member = self._resolve_member(member_code)
        interim_fields = self._resolve_interim(
            assignment_type, replaces_member_code, interim_sprint_count, member
        )

        obj.member = member
        obj.auto_assign = auto_assign
        obj.assignment_type = assignment_type
        obj.replaces_member = interim_fields["replaces_member"]
        obj.interim_sprint_count = interim_fields["interim_sprint_count"]
        obj.split_value = split_value
        obj.includes_in_budget = self._includes_in_budget(assignment_type)
        obj.notes = notes
        obj.updated_by = self.user
        obj.save(
            update_fields=[
                "member",
                "auto_assign",
                "assignment_type",
                "replaces_member",
                "interim_sprint_count",
                "split_value",
                "includes_in_budget",
                "notes",
                "updated_by",
                "updated_at",
            ]
        )
        obj.phase.recompute_is_split_incomplete()

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
        assignment_version_code: str,
    ) -> None:
        obj = self._get_assignment(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            assignment_version_code=assignment_version_code,
        )
        before = self._snapshot(obj)
        resource_code = self._resource_code(
            obj.phase.plan_project_team.plan_project.version.plan,
            obj.phase.plan_project_team.plan_project.version.version,
            obj,
        )
        # Captured before delete() — the FK reference would be gone afterward.
        phase = obj.phase
        obj.delete()
        phase.recompute_is_split_incomplete()

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=resource_code,
            before=before,
            actor=self.user,
        )
