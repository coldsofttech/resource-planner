from __future__ import annotations

from django.db.models import QuerySet, Sum
from django.db.models.functions import Coalesce

from apps.resource_plans.models import Allocation, AllocationSet


def get_allocation_by_code(code: str) -> Allocation | None:
    try:
        return Allocation.objects.select_related(
            "allocation_set",
            "allocation_set__version",
            "allocation_set__version__plan",
            "member",
            "placeholder_engineer",
            "team",
            "project",
            "project__programme",
            "phase",
            "sprint",
        ).get(code=code)
    except Allocation.DoesNotExist:
        return None


def get_allocations_for_set(
    allocation_set: AllocationSet, *, team_id: int | None = None
) -> QuerySet[Allocation]:
    qs = Allocation.objects.filter(allocation_set=allocation_set).select_related(
        "member",
        "placeholder_engineer",
        "team",
        "project",
        "project__programme",
        "phase",
        "sprint",
    )
    if team_id is not None:
        qs = qs.filter(team_id=team_id)
    return qs


def get_member_sprint_allocated_totals(
    allocation_set: AllocationSet,
    *,
    team_id: int | None = None,
    project_id: int | None = None,
):
    qs = Allocation.objects.filter(allocation_set=allocation_set, member__isnull=False)
    if team_id is not None:
        qs = qs.filter(team_id=team_id)
    if project_id is not None:
        qs = qs.filter(project_id=project_id)
    return qs.values("member_id", "sprint_id").annotate(
        total_days=Sum(Coalesce("override_days", "engine_days"))
    )


def get_team_placeholder_sprint_totals(
    allocation_set: AllocationSet, *, team_id: int | None = None
):
    """Sum(Coalesce(override_days, engine_days)) grouped by team+sprint for
    Allocation rows assigned to a PlaceholderEngineer rather than a real
    member — placeholders have no member identity, so this can only be
    team-scoped."""
    qs = Allocation.objects.filter(
        allocation_set=allocation_set, placeholder_engineer__isnull=False
    )
    if team_id is not None:
        qs = qs.filter(team_id=team_id)
    return qs.values("team_id", "sprint_id").annotate(
        total_days=Sum(Coalesce("override_days", "engine_days"))
    )
