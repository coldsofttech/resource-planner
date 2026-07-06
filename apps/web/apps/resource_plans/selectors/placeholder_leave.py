from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import PlaceholderLeave, PlanVersion


def get_placeholder_leaves_for_version(
    version: PlanVersion,
) -> QuerySet[PlaceholderLeave]:
    return (
        PlaceholderLeave.objects.filter(version=version)
        .select_related("member", "sprint")
        .order_by("member", "sprint")
    )


def get_placeholder_leave_for_slot(
    version: PlanVersion, member_id: int, sprint_id: int
) -> PlaceholderLeave | None:
    try:
        return PlaceholderLeave.objects.get(
            version=version, member_id=member_id, sprint_id=sprint_id
        )
    except PlaceholderLeave.DoesNotExist:
        return None


def get_placeholder_leave_by_code(code: str) -> PlaceholderLeave | None:
    try:
        return PlaceholderLeave.objects.select_related(
            "version", "version__plan", "member", "sprint"
        ).get(code=code)
    except PlaceholderLeave.DoesNotExist:
        return None
