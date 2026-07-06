from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.constants import EngineJobMode, EngineJobStatus
from apps.resource_plans.engine import ResourcePlanEngine
from apps.resource_plans.models import EngineJob, Plan, PlanVersion


class EngineJobService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "engine_job"

    def _snapshot(self, obj: EngineJob) -> dict:
        return {
            "plan_code": obj.plan.code,
            "version_number": obj.version.version,
            "status": obj.status,
            "mode": obj.mode,
            "include_current_sprint": obj.include_current_sprint,
            "dry_run": obj.dry_run,
            "duration_milliseconds": obj.duration_milliseconds,
        }

    def _resource_code(self, plan: Plan, job: EngineJob) -> str:
        return f"{plan.code}-{job.code}"

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

    def _get_engine_job(
        self, *, plan_code: str, version: int, job_code: str
    ) -> EngineJob:
        plan = self._get_plan(plan_code)
        obj = selectors.get_engine_job_by_code(job_code)
        if obj is None or obj.plan_id != plan.id:
            raise NotFoundException(
                resource="EngineJob", lookup_field="code", lookup_value=job_code
            )
        return obj

    def get(self, *, plan_code: str, version: int, job_code: str) -> EngineJob:
        return self._get_engine_job(
            plan_code=plan_code, version=version, job_code=job_code
        )

    def list_for_plan(
        self, *, plan_code: str, version: int, mode: str | None = None
    ) -> list[EngineJob]:
        plan = self._get_plan(plan_code)
        return list(selectors.get_engine_jobs_for_plan(plan, mode=mode))

    @transaction.atomic
    def create(
        self,
        *,
        plan_code: str,
        version: int,
        mode: str,
        include_current_sprint: bool,
    ) -> EngineJob:
        version_obj = self._get_version(plan_code, version)
        plan = version_obj.plan
        dry_run = mode == EngineJobMode.VALIDATE

        job = EngineJob.objects.create(
            plan=plan,
            version=version_obj,
            status=EngineJobStatus.RUNNING,
            mode=mode,
            include_current_sprint=include_current_sprint,
            dry_run=dry_run,
            started_at=timezone.now(),
            created_by=self.user,
            updated_by=self.user,
        )

        # Deferred until the row (and this whole transaction) has actually
        # committed — the background thread uses its own DB connection and
        # must not race the request thread's still-uncommitted insert.
        transaction.on_commit(lambda: ResourcePlanEngine.run_in_background(job.id))

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(plan, job),
            after=self._snapshot(job),
            actor=self.user,
        )
        return job

    @transaction.atomic
    def delete(self, *, plan_code: str, version: int, job_code: str) -> None:
        obj = self._get_engine_job(
            plan_code=plan_code, version=version, job_code=job_code
        )
        before = self._snapshot(obj)
        resource_code = self._resource_code(obj.plan, obj)
        obj.delete()

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=resource_code,
            before=before,
            actor=self.user,
        )
