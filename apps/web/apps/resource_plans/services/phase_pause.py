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
from apps.resource_plans.constants import PauseInputMode
from apps.resource_plans.models import (
    Plan,
    PlanPhase,
    PlanPhasePause,
    PlanVersion,
    PlanVersionTeam,
)
from apps.sprints import selectors as sprint_selectors
from apps.sprints.models import Sprint


class PlanPhasePauseService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "plan_phase_pause"

    def _snapshot(self, obj: PlanPhasePause) -> dict:
        return {
            "phase_code": obj.phase.code,
            "pause_from_code": obj.pause_from.code,
            "input_mode": obj.input_mode,
            "pause_until_sprint_code": (
                obj.pause_until_sprint.code if obj.pause_until_sprint_id else None
            ),
            "pause_sprint_count": obj.pause_sprint_count,
            "resume_sprint_code": obj.resume_sprint.code,
            "notes": obj.notes,
        }

    def _resource_code(
        self, plan: Plan, version_number: int, pause: PlanPhasePause
    ) -> str:
        return f"{plan.code}-v{version_number}-{pause.code}"

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

    def _get_pause(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
        pause_version_code: str,
    ) -> PlanPhasePause:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        obj = selectors.get_pause_by_code(pause_version_code)
        if obj is None or obj.phase_id != phase.id:
            raise NotFoundException(
                resource="PlanPhasePause",
                lookup_field="code",
                lookup_value=pause_version_code,
            )
        return obj

    def _resolve_pause_period(
        self,
        pause_from: Sprint,
        input_mode: str,
        pause_until_sprint_code: str | None,
        pause_sprint_count: int | None,
    ) -> tuple[dict[str, Sprint | int | None], Sprint]:
        fields: dict[str, Sprint | int | None]
        if input_mode == PauseInputMode.SPRINT:
            if not pause_until_sprint_code:
                raise ValidationException("A pause-until sprint must be selected.")
            pause_until_sprint = sprint_selectors.get_sprint_by_code(
                pause_until_sprint_code
            )
            if pause_until_sprint is None:
                raise NotFoundException(
                    resource="Sprint",
                    lookup_field="code",
                    lookup_value=pause_until_sprint_code,
                )
            if pause_until_sprint.sprint_number < pause_from.sprint_number:
                raise ValidationException(
                    "The pause-until sprint must not be before the pause-from sprint."
                )
            resume_number = pause_until_sprint.sprint_number + 1
            fields = {
                "pause_until_sprint": pause_until_sprint,
                "pause_sprint_count": None,
            }
        else:
            if not pause_sprint_count:
                raise ValidationException("A pause sprint count is required.")
            resume_number = pause_from.sprint_number + pause_sprint_count
            fields = {
                "pause_until_sprint": None,
                "pause_sprint_count": pause_sprint_count,
            }

        resume_sprint = sprint_selectors.get_sprint_by_number(resume_number)
        if resume_sprint is None:
            raise ValidationException(
                "No sprint exists to resume at — the pause extends beyond the "
                "last defined sprint."
            )
        return fields, resume_sprint

    def _check_no_overlap(
        self,
        phase: PlanPhase,
        pause_from: Sprint,
        resume_sprint: Sprint,
        exclude_pk: int | None = None,
    ) -> None:
        new_start = pause_from.sprint_number
        new_end = resume_sprint.sprint_number - 1
        for existing in selectors.get_pauses_for_phase(phase):
            if exclude_pk is not None and existing.pk == exclude_pk:
                continue
            existing_start = existing.pause_from.sprint_number
            existing_end = existing.resume_sprint.sprint_number - 1
            if new_start <= existing_end and existing_start <= new_end:
                raise ValidationException(
                    "This pause overlaps with an existing pause for this phase."
                )

    def list_for_phase(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
    ) -> list[PlanPhasePause]:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return list(selectors.get_pauses_for_phase(phase))

    @transaction.atomic
    def create(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        team_version_code: str,
        phase_version_code: str,
        pause_from_code: str,
        input_mode: str,
        pause_until_sprint_code: str | None,
        pause_sprint_count: int | None,
        notes: str,
    ) -> PlanPhasePause:
        phase = self._get_phase(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        pause_from = sprint_selectors.get_sprint_by_code(pause_from_code)
        if pause_from is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=pause_from_code
            )

        if selectors.pause_from_exists(phase, pause_from):
            raise AlreadyExistsException(
                detail="A pause already starts from this sprint for this phase."
            )

        fields, resume_sprint = self._resolve_pause_period(
            pause_from, input_mode, pause_until_sprint_code, pause_sprint_count
        )
        self._check_no_overlap(phase, pause_from, resume_sprint)

        obj = PlanPhasePause.objects.create(
            phase=phase,
            pause_from=pause_from,
            input_mode=input_mode,
            resume_sprint=resume_sprint,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        # is_beyond_fy lives on the pause row itself, not on the phase.
        obj.recompute_is_beyond_fy()

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
        pause_version_code: str,
        pause_from_code: str,
        input_mode: str,
        pause_until_sprint_code: str | None,
        pause_sprint_count: int | None,
        notes: str,
    ) -> PlanPhasePause:
        obj = self._get_pause(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            pause_version_code=pause_version_code,
        )
        before = self._snapshot(obj)

        pause_from = sprint_selectors.get_sprint_by_code(pause_from_code)
        if pause_from is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=pause_from_code
            )

        if selectors.pause_from_exists(obj.phase, pause_from, exclude_pk=obj.pk):
            raise AlreadyExistsException(
                detail="A pause already starts from this sprint for this phase."
            )

        fields, resume_sprint = self._resolve_pause_period(
            pause_from, input_mode, pause_until_sprint_code, pause_sprint_count
        )
        self._check_no_overlap(obj.phase, pause_from, resume_sprint, exclude_pk=obj.pk)

        obj.pause_from = pause_from
        obj.input_mode = input_mode
        obj.pause_until_sprint = fields["pause_until_sprint"]
        obj.pause_sprint_count = fields["pause_sprint_count"]
        obj.resume_sprint = resume_sprint
        obj.notes = notes
        obj.updated_by = self.user
        obj.save(
            update_fields=[
                "pause_from",
                "input_mode",
                "pause_until_sprint",
                "pause_sprint_count",
                "resume_sprint",
                "notes",
                "updated_by",
                "updated_at",
            ]
        )
        obj.recompute_is_beyond_fy()

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
        pause_version_code: str,
    ) -> None:
        obj = self._get_pause(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            pause_version_code=pause_version_code,
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
