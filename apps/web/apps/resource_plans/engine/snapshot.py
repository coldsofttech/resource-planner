from __future__ import annotations

import logging
import threading
from decimal import Decimal

from django.db import close_old_connections, transaction
from django.utils import timezone

from apps.resource_plans import selectors
from apps.resource_plans.constants import SnapshotStatus
from apps.resource_plans.models import (
    MemberCapacity,
    Snapshot,
    SnapshotAllocation,
    SnapshotCapacity,
)
from apps.teams import selectors as team_selectors

logger = logging.getLogger(__name__)

_BATCH_SIZE = 500


class SnapshotEngine:
    """Denormalizes a plan version's active allocation set (allocations +
    capacity) into a Snapshot's child rows. Runs on a background thread
    (run_in_background()) so generation never holds the request/response
    cycle open — the caller must launch it from `transaction.on_commit()`
    so the thread's own DB connection can already see the Snapshot row."""

    @classmethod
    def run_in_background(cls, snapshot_id: int) -> None:
        threading.Thread(target=cls.run, args=(snapshot_id,), daemon=True).start()

    @classmethod
    def run(cls, snapshot_id: int) -> None:
        close_old_connections()
        try:
            snapshot = Snapshot.objects.select_related("plan", "version").get(
                id=snapshot_id
            )
        except Snapshot.DoesNotExist:
            logger.error("Snapshot id=%s not found for snapshot run.", snapshot_id)
            return

        try:
            cls()._run_job(snapshot)
        finally:
            close_old_connections()

    def _run_job(self, snapshot: Snapshot) -> None:
        started_at = timezone.now()
        Snapshot.objects.filter(id=snapshot.id).update(
            status=SnapshotStatus.IN_PROGRESS, started_at=started_at
        )

        try:
            allocation_set = (
                selectors.get_active_allocation_set_for_version(snapshot.version)
                or selectors.get_allocation_sets_for_version(snapshot.version).first()
            )
            if allocation_set is None:
                raise ValueError(
                    "No allocation set exists for this version — run the engine "
                    "first before taking a snapshot."
                )

            # select_related("member__profile") merges into the selector's
            # own select_related list rather than replacing it — avoids an
            # N+1 profile lookup per allocation when denormalizing names.
            allocation_rows = list(
                selectors.get_allocations_for_set(allocation_set).select_related(
                    "member__profile"
                )
            )
            capacity_rows = list(
                MemberCapacity.objects.filter(version=snapshot.version).select_related(
                    "member", "member__profile", "sprint"
                )
            )

            # MemberCapacity has no team FK — resolve each member's team
            # name(s) via the version's configured teams, same approach
            # UtilisationService/GridService use.
            member_team_names: dict[int, str] = {}
            for team in selectors.get_teams_for_version(snapshot.version):
                for member in team_selectors.get_active_members_for_team(team):
                    existing = member_team_names.get(member.id)
                    member_team_names[member.id] = (
                        f"{existing}, {team.name}" if existing else team.name
                    )

            snapshot_allocations = [
                SnapshotAllocation(
                    snapshot=snapshot,
                    sprint_number=alloc.sprint.sprint_number,
                    sprint_name=alloc.sprint.name,
                    member_name=(
                        alloc.member.profile.display_name or alloc.member.email
                        if alloc.member_id
                        else alloc.placeholder_engineer.name
                    ),
                    team_name=alloc.team.name,
                    project_name=alloc.project.name,
                    programme_name=(
                        alloc.project.programme.name
                        if alloc.project.programme_id
                        else ""
                    ),
                    phase_name=alloc.phase.name if alloc.phase_id else "",
                    assignment_type=alloc.assignment_type,
                    includes_in_budget=alloc.includes_in_budget,
                    days=alloc.effective_days,
                    is_override=alloc.override_days is not None,
                    is_placeholder=alloc.placeholder_engineer_id is not None,
                )
                for alloc in allocation_rows
            ]
            SnapshotAllocation.objects.bulk_create(
                snapshot_allocations, batch_size=_BATCH_SIZE
            )

            snapshot_capacities = [
                SnapshotCapacity(
                    snapshot=snapshot,
                    sprint_number=cap.sprint.sprint_number,
                    sprint_name=cap.sprint.name,
                    member_name=(cap.member.profile.display_name or cap.member.email),
                    team_name=member_team_names.get(cap.member_id, ""),
                    working_days=cap.working_days,
                    holiday_days=cap.holiday_days,
                    leave_days=cap.leave_days,
                    placeholder_leave_days=cap.placeholder_leave_days,
                    net_capacity=cap.net_capacity,
                )
                for cap in capacity_rows
            ]
            SnapshotCapacity.objects.bulk_create(
                snapshot_capacities, batch_size=_BATCH_SIZE
            )

            total_allocation_days = sum(
                (a.days for a in snapshot_allocations), Decimal("0")
            )
            total_members = len({a.member_name for a in snapshot_allocations})
            total_projects = len({a.project_name for a in snapshot_allocations})
            total_sprints = len({a.sprint_number for a in snapshot_allocations})

            completed_at = timezone.now()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            with transaction.atomic():
                Snapshot.objects.filter(id=snapshot.id).update(
                    status=SnapshotStatus.COMPLETE,
                    completed_at=completed_at,
                    duration_milliseconds=duration_ms,
                    total_allocation_days=total_allocation_days,
                    total_members=total_members,
                    total_projects=total_projects,
                    total_sprints=total_sprints,
                )
        except Exception as exc:
            logger.exception(
                "Snapshot generation failed for snapshot %s", snapshot.code
            )
            now = timezone.now()
            duration_ms = int((now - started_at).total_seconds() * 1000)
            Snapshot.objects.filter(id=snapshot.id).update(
                status=SnapshotStatus.FAILED,
                completed_at=now,
                duration_milliseconds=duration_ms,
                error_log=[{"message": str(exc), "occurred_at": now.isoformat()}],
            )
