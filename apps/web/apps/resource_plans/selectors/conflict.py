from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import AllocationSet, Conflict


def get_conflicts_for_set(allocation_set: AllocationSet) -> QuerySet[Conflict]:
    return (
        Conflict.objects.filter(allocation_set=allocation_set)
        .select_related(
            "affected_project",
            "affected_phase",
            "affected_member",
            "affected_member__profile",
            "affected_sprint",
            "affected_team",
        )
        .order_by("severity", "-created_at")
    )


def get_conflict_by_code(code: str) -> Conflict | None:
    try:
        return Conflict.objects.select_related(
            "allocation_set",
            "allocation_set__version",
            "allocation_set__version__plan",
            "affected_project",
            "affected_phase",
            "affected_member",
            "affected_member__profile",
            "affected_sprint",
            "affected_team",
        ).get(code=code)
    except Conflict.DoesNotExist:
        return None
