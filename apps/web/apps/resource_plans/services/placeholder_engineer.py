from __future__ import annotations

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService
from apps.resource_plans.constants import ManpowerRequestStatus
from apps.resource_plans.models import (
    Allocation,
    EngineerHirePlaceholder,
    ManpowerRequest,
)
from apps.resource_plans.services.placeholder_engineer_absence import (
    PlaceholderEngineerAbsenceService,
)
from apps.sprints import selectors as sprint_selectors
from apps.sprints.models import Sprint
from apps.users.models import User


class PlaceholderEngineerService(AuditableService):
    """The hire-placeholder workflow — turns a ManpowerRequest into a
    deliberate "we're hiring for this" record (EngineerHirePlaceholder),
    distinct from the auto-assign fallback slot (PlaceholderEngineer) created
    inline by AllocationEngineService. See
    docs/architecture/resource-plan-engine.md's "naming collision" section.
    """

    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "engineer_hire_placeholder"

    def _snapshot(self, obj: EngineerHirePlaceholder) -> dict:
        replaced_by_profile = getattr(obj.replaced_by, "profile", None)
        return {
            "sequence_number": obj.sequence_number,
            "display_name": obj.display_name,
            "team_code": obj.team.code,
            "onboard_sprint_code": (
                obj.onboard_sprint.code if obj.onboard_sprint_id else None
            ),
            "engine_suggested_sprint_code": (
                obj.engine_suggested_sprint.code
                if obj.engine_suggested_sprint_id
                else None
            ),
            "replaced_by_code": (
                replaced_by_profile.code if replaced_by_profile else None
            ),
            "replaced_at": obj.replaced_at.isoformat() if obj.replaced_at else None,
        }

    @staticmethod
    def _suggest_sprint(manpower_request: ManpowerRequest) -> Sprint | None:
        fy = manpower_request.allocation_set.version.plan.financial_year
        return sprint_selectors.get_first_sprint_starting_on_or_after(
            fy.code, manpower_request.created_at.date()
        )

    @staticmethod
    def _resolve_sprint(sprint_id: int) -> Sprint:
        try:
            return Sprint.objects.get(id=sprint_id)
        except Sprint.DoesNotExist:
            raise NotFoundException(
                resource="Sprint", lookup_field="id", lookup_value=sprint_id
            ) from None

    @staticmethod
    def _resolve_member(member_id: int) -> User:
        try:
            return User.objects.get(id=member_id)
        except User.DoesNotExist:
            raise NotFoundException(
                resource="Member", lookup_field="id", lookup_value=member_id
            ) from None

    @transaction.atomic
    def create_from_manpower_request(
        self, manpower_request: ManpowerRequest, onboard_sprint_id: int | None = None
    ) -> EngineerHirePlaceholder:
        version = manpower_request.allocation_set.version
        next_seq = (
            EngineerHirePlaceholder.objects.filter(version=version).aggregate(
                max_seq=Max("sequence_number")
            )["max_seq"]
            or 0
        ) + 1

        engine_suggested_sprint = self._suggest_sprint(manpower_request)
        onboard_sprint = (
            self._resolve_sprint(onboard_sprint_id)
            if onboard_sprint_id is not None
            else engine_suggested_sprint
        )

        obj = EngineerHirePlaceholder.objects.create(
            version=version,
            sequence_number=next_seq,
            display_name=f"Engineer {next_seq}",
            team=manpower_request.team,
            manpower_request=manpower_request,
            onboard_sprint=onboard_sprint,
            engine_suggested_sprint=engine_suggested_sprint,
            created_by=self.user,
            updated_by=self.user,
        )

        if onboard_sprint is not None:
            PlaceholderEngineerAbsenceService(user=self.user).generate_absences(obj)

        if manpower_request.status != ManpowerRequestStatus.HIRING:
            manpower_request.status = ManpowerRequestStatus.HIRING
            manpower_request.save(update_fields=["status"])

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update_onboard_sprint(
        self, hire_placeholder: EngineerHirePlaceholder, onboard_sprint_id: int
    ) -> EngineerHirePlaceholder:
        before = self._snapshot(hire_placeholder)
        onboard_sprint = self._resolve_sprint(onboard_sprint_id)

        hire_placeholder.onboard_sprint = onboard_sprint
        hire_placeholder.updated_by = self.user
        hire_placeholder.save(
            update_fields=["onboard_sprint", "updated_by", "updated_at"]
        )

        PlaceholderEngineerAbsenceService(user=self.user).generate_absences(
            hire_placeholder
        )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=hire_placeholder.code,
            before=before,
            after=self._snapshot(hire_placeholder),
            actor=self.user,
        )
        return hire_placeholder

    @transaction.atomic
    def replace_with_hire(
        self, hire_placeholder: EngineerHirePlaceholder, member_id: int
    ) -> EngineerHirePlaceholder:
        member = self._resolve_member(member_id)
        manpower_request = hire_placeholder.manpower_request
        if manpower_request is None or manpower_request.phase_id is None:
            raise ValidationException(
                "Cannot replace a hire placeholder that has no originating phase."
            )

        before = self._snapshot(hire_placeholder)

        Allocation.objects.filter(
            phase=manpower_request.phase,
            placeholder_engineer__isnull=False,
        ).update(member=member, placeholder_engineer=None)

        hire_placeholder.replaced_by = member
        hire_placeholder.replaced_at = timezone.now()
        hire_placeholder.updated_by = self.user
        hire_placeholder.save(
            update_fields=["replaced_by", "replaced_at", "updated_by", "updated_at"]
        )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=hire_placeholder.code,
            before=before,
            after=self._snapshot(hire_placeholder),
            actor=self.user,
        )
        return hire_placeholder
