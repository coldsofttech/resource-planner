from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.constants import AllocationSetStatus
from apps.resource_plans.models import AllocationSet, PlanVersion


def get_allocation_sets_for_version(version: PlanVersion) -> QuerySet[AllocationSet]:
    return (
        AllocationSet.objects.filter(version=version)
        .select_related("engine_job")
        .order_by("-created_at")
    )


def get_allocation_set_by_code(code: str) -> AllocationSet | None:
    try:
        return AllocationSet.objects.select_related(
            "version", "version__plan", "engine_job"
        ).get(code=code)
    except AllocationSet.DoesNotExist:
        return None


def get_active_allocation_set_for_version(version: PlanVersion) -> AllocationSet | None:
    return (
        AllocationSet.objects.filter(version=version, status=AllocationSetStatus.ACTIVE)
        .select_related("engine_job")
        .first()
    )
