from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService, paginate_queryset
from apps.core.types import ListParams, PaginatedResult
from apps.resource_plans import selectors
from apps.resource_plans.constants import ManpowerRequestStatus
from apps.resource_plans.models import (
    AllocationSet,
    Conflict,
    EngineerHirePlaceholder,
    ManpowerRequest,
    Plan,
    PlanVersion,
)
from apps.resource_plans.selectors.manpower_request import (
    get_manpower_request_for_conflict,
)
from apps.resource_plans.services.placeholder_engineer import PlaceholderEngineerService
from apps.sprints import selectors as sprint_selectors


class ManpowerRequestService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "manpower_request"

    def _snapshot(self, obj: ManpowerRequest) -> dict:
        return {
            "team_code": obj.team.code,
            "phase_code": obj.phase.code if obj.phase_id else None,
            "sprints_needed": obj.sprints_needed,
            "days_needed": float(obj.days_needed),
            "status": obj.status,
            "resolution_notes": obj.resolution_notes,
        }

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

    def _get_manpower_request(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        manpower_request_code: str,
    ) -> ManpowerRequest:
        allocation_set = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        obj = selectors.get_manpower_request_by_code(manpower_request_code)
        if obj is None or obj.allocation_set_id != allocation_set.id:
            raise NotFoundException(
                resource="ManpowerRequest",
                lookup_field="code",
                lookup_value=manpower_request_code,
            )
        return obj

    def list_for_set(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        params: ListParams | None = None,
    ) -> PaginatedResult[ManpowerRequest]:
        params = params or ListParams()
        allocation_set = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        qs = selectors.get_manpower_requests_for_set(allocation_set)

        status = params.filters.get("status")
        if status:
            qs = qs.filter(status=status)

        team_code = params.filters.get("team")
        if team_code:
            qs = qs.filter(team__code=team_code)

        return paginate_queryset(qs, params.page, params.page_size)

    def get(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        manpower_request_code: str,
    ) -> ManpowerRequest:
        return self._get_manpower_request(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
            manpower_request_code=manpower_request_code,
        )

    def hire_by_code(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        manpower_request_code: str,
        onboard_sprint_code: str | None = None,
    ) -> EngineerHirePlaceholder:
        manpower_request = self._get_manpower_request(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
            manpower_request_code=manpower_request_code,
        )
        onboard_sprint_id = None
        if onboard_sprint_code:
            sprint = sprint_selectors.get_sprint_by_code(onboard_sprint_code)
            if sprint is None:
                raise NotFoundException(
                    resource="Sprint",
                    lookup_field="code",
                    lookup_value=onboard_sprint_code,
                )
            onboard_sprint_id = sprint.id
        return self.hire(manpower_request, onboard_sprint_id)

    def rebalance_by_code(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        manpower_request_code: str,
        notes: str = "",
    ) -> ManpowerRequest:
        manpower_request = self._get_manpower_request(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
            manpower_request_code=manpower_request_code,
        )
        return self.rebalance(manpower_request, notes)

    def dismiss_by_code(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        manpower_request_code: str,
        notes: str = "",
    ) -> ManpowerRequest:
        manpower_request = self._get_manpower_request(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
            manpower_request_code=manpower_request_code,
        )
        return self.dismiss(manpower_request, notes)

    @transaction.atomic
    def create_from_conflict(self, conflict: Conflict) -> ManpowerRequest:
        existing = get_manpower_request_for_conflict(conflict)
        if existing is not None:
            return existing

        if conflict.affected_team is None:
            raise ValidationException(
                "Cannot raise a manpower request for a conflict with no affected team."
            )

        engine_data = conflict.engine_data or {}
        days_needed = Decimal(
            str(engine_data.get("excess_days") or engine_data.get("total_days") or "0")
        )
        sprints_needed = int(engine_data.get("sprint_count") or 1)

        obj = ManpowerRequest.objects.create(
            allocation_set=conflict.allocation_set,
            conflict=conflict,
            team=conflict.affected_team,
            phase=conflict.affected_phase,
            sprints_needed=sprints_needed,
            days_needed=days_needed,
        )

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    def hire(
        self, manpower_request: ManpowerRequest, onboard_sprint_id: int | None = None
    ) -> EngineerHirePlaceholder:
        """Delegates to PlaceholderEngineerService — turns this ManpowerRequest
        into a deliberate "we're hiring for this" EngineerHirePlaceholder record
        and flips the request's status to Hiring.
        """
        return PlaceholderEngineerService(user=self.user).create_from_manpower_request(
            manpower_request, onboard_sprint_id
        )

    def rebalance(
        self, manpower_request: ManpowerRequest, notes: str = ""
    ) -> ManpowerRequest:
        return self._transition(
            manpower_request, ManpowerRequestStatus.REBALANCED, notes
        )

    def dismiss(
        self, manpower_request: ManpowerRequest, notes: str = ""
    ) -> ManpowerRequest:
        return self._transition(
            manpower_request, ManpowerRequestStatus.DISMISSED, notes
        )

    @transaction.atomic
    def _transition(
        self, manpower_request: ManpowerRequest, status: str, notes: str
    ) -> ManpowerRequest:
        before = self._snapshot(manpower_request)
        manpower_request.status = status
        manpower_request.resolution_notes = notes
        manpower_request.resolved_at = timezone.now()
        manpower_request.save(
            update_fields=["status", "resolution_notes", "resolved_at"]
        )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=manpower_request.code,
            before=before,
            after=self._snapshot(manpower_request),
            actor=self.user,
        )
        return manpower_request
