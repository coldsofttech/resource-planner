from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.constants import AllocationSetStatus
from apps.resource_plans.models import Allocation, AllocationSet, Plan, PlanVersion
from apps.resource_plans.services.conflict_detection import ConflictDetectionService


class AllocationService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "allocation"

    def _snapshot(self, obj: Allocation) -> dict:
        return {
            "engine_days": float(obj.engine_days),
            "override_days": (
                float(obj.override_days) if obj.override_days is not None else None
            ),
            "override_notes": obj.override_notes,
        }

    def _resource_code(self, plan: Plan, version_number: int, obj: Allocation) -> str:
        return f"{plan.code}-v{version_number}-{obj.code}"

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

    def _get_allocation(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        allocation_code: str,
    ) -> Allocation:
        alloc_set = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        obj = selectors.get_allocation_by_code(allocation_code)
        if obj is None or obj.allocation_set_id != alloc_set.id:
            raise NotFoundException(
                resource="Allocation",
                lookup_field="code",
                lookup_value=allocation_code,
            )
        return obj

    @transaction.atomic
    def override(
        self,
        *,
        plan_code: str,
        version: int,
        allocation_set_code: str,
        allocation_code: str,
        override_days: Decimal | None,
        notes: str,
    ) -> Allocation:
        obj = self._get_allocation(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
            allocation_code=allocation_code,
        )
        if obj.allocation_set.status != AllocationSetStatus.DRAFT:
            raise ValidationException(
                "Only allocations in a draft allocation set can be overridden. "
                "Run the engine to create a new draft set for editing."
            )

        before = self._snapshot(obj)

        obj.override_days = override_days
        obj.override_notes = notes if override_days is not None else ""
        obj.overridden_at = timezone.now() if override_days is not None else None
        obj.save(update_fields=["override_days", "override_notes", "overridden_at"])

        ConflictDetectionService().refresh_threshold_for_alloc_set(obj.allocation_set)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                obj.allocation_set.version.plan,
                obj.allocation_set.version.version,
                obj,
            ),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj
