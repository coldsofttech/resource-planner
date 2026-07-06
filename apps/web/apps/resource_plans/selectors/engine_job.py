from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import EngineJob, Plan


def get_engine_jobs_for_plan(
    plan: Plan, *, mode: str | None = None
) -> QuerySet[EngineJob]:
    qs = (
        EngineJob.objects.filter(plan=plan)
        .select_related("version")
        .prefetch_related("steps")
    )
    if mode:
        qs = qs.filter(mode=mode)
    return qs


def get_engine_job_by_code(code: str) -> EngineJob | None:
    try:
        return (
            EngineJob.objects.select_related("plan", "version")
            .prefetch_related("steps")
            .get(code=code)
        )
    except EngineJob.DoesNotExist:
        return None
