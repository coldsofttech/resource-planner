from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import AllocationSet, Conflict, ManpowerRequest


def get_manpower_request_for_conflict(conflict: Conflict) -> ManpowerRequest | None:
    return (
        ManpowerRequest.objects.filter(conflict=conflict)
        .select_related("team", "phase")
        .first()
    )


def get_manpower_requests_for_set(
    allocation_set: AllocationSet,
) -> QuerySet[ManpowerRequest]:
    return (
        ManpowerRequest.objects.filter(allocation_set=allocation_set)
        .select_related("team", "phase", "conflict")
        .order_by("-created_at")
    )


def get_manpower_request_by_code(code: str) -> ManpowerRequest | None:
    try:
        return ManpowerRequest.objects.select_related(
            "allocation_set",
            "allocation_set__version",
            "allocation_set__version__plan",
            "team",
            "phase",
            "conflict",
        ).get(code=code)
    except ManpowerRequest.DoesNotExist:
        return None
