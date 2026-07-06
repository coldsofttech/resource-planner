from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import PlanVersion, Snapshot, SnapshotAllocation


def get_snapshots_for_version(version: PlanVersion) -> QuerySet[Snapshot]:
    return Snapshot.objects.filter(version=version).order_by("-initiated_at")


def get_snapshot_by_code(code: str) -> Snapshot | None:
    try:
        return Snapshot.objects.select_related("plan", "version").get(code=code)
    except Snapshot.DoesNotExist:
        return None


def get_snapshot_allocations(
    snapshot: Snapshot,
    *,
    sprint_number: int | None = None,
    member_name: str | None = None,
    team_name: str | None = None,
    project_name: str | None = None,
    assignment_type: str | None = None,
) -> QuerySet[SnapshotAllocation]:
    qs = SnapshotAllocation.objects.filter(snapshot=snapshot)
    if sprint_number is not None:
        qs = qs.filter(sprint_number=sprint_number)
    if member_name:
        qs = qs.filter(member_name=member_name)
    if team_name:
        qs = qs.filter(team_name=team_name)
    if project_name:
        qs = qs.filter(project_name=project_name)
    if assignment_type:
        qs = qs.filter(assignment_type=assignment_type)
    return qs


def get_snapshot_allocation_filter_options(snapshot: Snapshot) -> dict:
    # `.order_by()` clears SnapshotAllocation.Meta's default ordering — left
    # in place, Django folds those extra columns into the query for ordering
    # purposes, which silently breaks single/double-column `.distinct()`.
    rows = SnapshotAllocation.objects.filter(snapshot=snapshot).order_by()
    sprints = rows.values_list("sprint_number", "sprint_name").distinct()
    return {
        "sprints": sorted(
            ({"value": number, "label": name} for number, name in sprints),
            key=lambda s: s["value"],
        ),
        "members": sorted(rows.values_list("member_name", flat=True).distinct()),
        "teams": sorted(rows.values_list("team_name", flat=True).distinct()),
        "projects": sorted(rows.values_list("project_name", flat=True).distinct()),
    }
