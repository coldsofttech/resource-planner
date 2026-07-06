from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import MemberCapacity, PlanVersion


def get_member_capacities_for_version(
    version: PlanVersion, *, member_ids: list[int] | None = None
) -> QuerySet[MemberCapacity]:
    qs = MemberCapacity.objects.filter(version=version).select_related(
        "member", "sprint"
    )
    if member_ids is not None:
        qs = qs.filter(member_id__in=member_ids)
    return qs
