from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.constants import AllocationSetStatus
from apps.resource_plans.models import AllocationSet, Plan, PlanVersion


class AllocationSetService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "allocation_set"

    def _snapshot(self, obj: AllocationSet) -> dict:
        return {
            "version_number": obj.version.version,
            "engine_job_code": obj.engine_job.code,
            "status": obj.status,
            "activated_at": obj.activated_at.isoformat() if obj.activated_at else None,
            "notes": obj.notes,
        }

    def _resource_code(
        self, plan: Plan, version_number: int, obj: AllocationSet
    ) -> str:
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

    def list_for_version(self, *, plan_code: str, version: int) -> list[AllocationSet]:
        version_obj = self._get_version(plan_code, version)
        return list(selectors.get_allocation_sets_for_version(version_obj))

    def get(
        self, *, plan_code: str, version: int, allocation_set_code: str
    ) -> AllocationSet:
        return self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )

    @transaction.atomic
    def activate(
        self, *, plan_code: str, version: int, allocation_set_code: str
    ) -> AllocationSet:
        obj = self._get_allocation_set(
            plan_code=plan_code,
            version=version,
            allocation_set_code=allocation_set_code,
        )
        if obj.status != AllocationSetStatus.DRAFT:
            raise ValidationException("Only a draft allocation set can be activated.")

        before = self._snapshot(obj)

        # Any previously-active set for this version is superseded — only one
        # allocation set can be active per version at a time.
        AllocationSet.objects.filter(
            version=obj.version, status=AllocationSetStatus.ACTIVE
        ).exclude(pk=obj.pk).update(status=AllocationSetStatus.SUPERSEDED)

        obj.status = AllocationSetStatus.ACTIVE
        obj.activated_at = timezone.now()
        obj.updated_by = self.user
        obj.save(update_fields=["status", "activated_at", "updated_by", "updated_at"])

        AuditService.log_activate(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                obj.version.plan, obj.version.version, obj
            ),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj
