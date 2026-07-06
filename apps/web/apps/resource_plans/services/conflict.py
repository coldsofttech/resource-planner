from __future__ import annotations

from django.db.models import Q

from apps.core.exceptions import NotFoundException
from apps.core.services import AuditableService, paginate_queryset
from apps.core.types import ListParams, PaginatedResult
from apps.resource_plans import selectors
from apps.resource_plans.models import AllocationSet, Conflict, Plan, PlanVersion
from apps.resource_plans.services.conflict_resolution import ConflictResolutionService


class ConflictService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "conflict"

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

    def _get_conflict(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        conflict_code: str,
    ) -> Conflict:
        allocation_set = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        obj = selectors.get_conflict_by_code(conflict_code)
        if obj is None or obj.allocation_set_id != allocation_set.id:
            raise NotFoundException(
                resource="Conflict", lookup_field="code", lookup_value=conflict_code
            )
        return obj

    def list_for_set(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        params: ListParams | None = None,
    ) -> PaginatedResult[Conflict]:
        params = params or ListParams()
        allocation_set = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        qs = selectors.get_conflicts_for_set(allocation_set)

        conflict_type = params.filters.get("type")
        if conflict_type:
            qs = qs.filter(conflict_type=conflict_type)

        severity = params.filters.get("severity")
        if severity not in (None, ""):
            qs = qs.filter(severity=severity)

        status = params.filters.get("status")
        if status:
            qs = qs.filter(status=status)

        if params.search:
            qs = qs.filter(Q(description__icontains=params.search))

        return paginate_queryset(qs, params.page, params.page_size)

    def get(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        conflict_code: str,
    ) -> Conflict:
        return self._get_conflict(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
            conflict_code=conflict_code,
        )

    def resolve(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        conflict_code: str,
        resolution_type: str,
        notes: str = "",
        extra_data: dict | None = None,
    ) -> Conflict:
        conflict = self._get_conflict(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
            conflict_code=conflict_code,
        )
        return ConflictResolutionService(user=self.user).resolve(
            conflict, resolution_type, notes, extra_data
        )
