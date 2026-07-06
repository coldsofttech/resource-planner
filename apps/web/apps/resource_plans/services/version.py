from __future__ import annotations

from django.db import transaction
from django.db.models import QuerySet

from apps.audit.models import Audit
from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.constants import VersionStatus
from apps.resource_plans.models import Plan, PlanVersion


class ResourcePlanVersionService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "resource_plan_version"

    def _snapshot(self, version: PlanVersion) -> dict:
        return {
            "plan_code": version.plan.code,
            "version": version.version,
            "status": version.status,
            "threshold_percentage": float(version.threshold_percentage),
            "cloned_from_version": (
                version.cloned_from.version if version.cloned_from_id else None
            ),
        }

    def _resource_code(self, plan: Plan, version_number: int) -> str:
        return f"{plan.code}-v{version_number}"

    def _get_plan(self, plan_code: str) -> Plan:
        obj = selectors.get_resource_plan_by_code(plan_code)
        if obj is None:
            raise NotFoundException(
                resource="Plan", lookup_field="code", lookup_value=plan_code
            )
        return obj

    def get(self, plan_code: str, version: int) -> PlanVersion:
        plan = self._get_plan(plan_code)
        obj = selectors.get_version_by_number(plan, version)
        if obj is None:
            raise NotFoundException(
                resource="PlanVersion",
                lookup_field="version",
                lookup_value=version,
            )
        return obj

    @transaction.atomic
    def create(self, *, plan_code: str, threshold_percentage: float) -> PlanVersion:
        plan = self._get_plan(plan_code)
        latest = selectors.get_latest_version(plan)
        next_version = (latest.version + 1) if latest else 1

        obj = PlanVersion.objects.create(
            plan=plan,
            version=next_version,
            status=VersionStatus.DRAFT,
            threshold_percentage=threshold_percentage,
            created_by=self.user,
            updated_by=self.user,
        )

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(plan, obj.version),
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def activate(self, *, plan_code: str, version: int) -> PlanVersion:
        obj = self.get(plan_code, version)
        if obj.status == VersionStatus.LOCKED:
            raise ValidationException("A locked version cannot be activated.")

        before = self._snapshot(obj)
        obj.status = VersionStatus.ACTIVE
        obj.updated_by = self.user
        obj.save(update_fields=["status", "updated_by", "updated_at"])

        AuditService.log_activate(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(obj.plan, obj.version),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def restore(self, *, plan_code: str, version: int) -> PlanVersion:
        source = self.get(plan_code, version)
        plan = source.plan
        latest = selectors.get_latest_version(plan)
        next_version = (latest.version + 1) if latest else 1

        new_obj = PlanVersion.objects.create(
            plan=plan,
            version=next_version,
            status=VersionStatus.DRAFT,
            cloned_from=source,
            threshold_percentage=source.threshold_percentage,
            has_leave_overrides=source.has_leave_overrides,
            has_allocation_overrides=source.has_allocation_overrides,
            created_by=self.user,
            updated_by=self.user,
        )

        AuditService.log_restore(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(plan, new_obj.version),
            before=self._snapshot(source),
            after=self._snapshot(new_obj),
            actor=self.user,
        )
        return new_obj

    @transaction.atomic
    def lock(self, *, plan_code: str, version: int) -> PlanVersion:
        obj = self.get(plan_code, version)
        if obj.status != VersionStatus.ACTIVE:
            raise ValidationException("Only an active version can be locked.")

        before = self._snapshot(obj)
        obj.status = VersionStatus.LOCKED
        obj.updated_by = self.user
        obj.save(update_fields=["status", "updated_by", "updated_at"])

        AuditService.log_lock(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(obj.plan, obj.version),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, *, plan_code: str, version: int) -> None:
        obj = self.get(plan_code, version)
        if obj.status != VersionStatus.DRAFT:
            raise ValidationException("Only a draft version can be deleted.")

        plan = obj.plan
        version_number = obj.version
        before = self._snapshot(obj)
        obj.delete()

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(plan, version_number),
            before=before,
            actor=self.user,
        )

    def history(self, *, plan_code: str) -> QuerySet[Audit]:
        plan = self._get_plan(plan_code)
        return selectors.get_version_history(plan)
