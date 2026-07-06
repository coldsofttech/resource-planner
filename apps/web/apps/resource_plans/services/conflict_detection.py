from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.resource_plans import selectors
from apps.resource_plans.constants import ConflictSeverity, ConflictType
from apps.resource_plans.models import (
    Allocation,
    AllocationSet,
    Conflict,
    EngineJob,
    ManpowerRequest,
    PlaceholderEngineer,
    PlanVersion,
)
from apps.resource_plans.selectors import phase as phase_selectors
from apps.resource_plans.selectors import version_team as version_team_selectors


class ConflictDetectionService:
    """Backs Engine Step 7 (Detect Conflicts) — a fresh detection pass over an
    AllocationSet's Allocation rows. Conflicts are fully disposable and
    regenerated every run, never an audit trail.

    COMPETING_PRIORITY, BUDGET_EXCEEDED, and DEPENDENCY_VIOLATED are reserved
    ConflictType values with no detection logic yet — see
    docs/architecture/resource-plan-engine.md.
    """

    def detect_and_persist(
        self, version: PlanVersion, alloc_set: AllocationSet, job: EngineJob
    ) -> list[Conflict]:
        with transaction.atomic():
            Conflict.objects.filter(allocation_set=alloc_set).delete()

            conflicts: list[Conflict] = []
            conflicts += self._detect_capacity_exceeded(version, alloc_set, job)
            conflicts += self._detect_threshold_breach(version, alloc_set, job)
            conflicts += self._detect_timeline_breach(version, alloc_set, job)
            conflicts += self._detect_unresolvable_gap(alloc_set, job)
        return conflicts

    def refresh_threshold_for_alloc_set(
        self, alloc_set: AllocationSet
    ) -> list[Conflict]:
        """Lightweight re-check of only THRESHOLD_BREACH conflicts — used after a
        manual Allocation.override_days edit so a full engine re-run isn't
        required just to re-evaluate budget thresholds.
        """
        with transaction.atomic():
            Conflict.objects.filter(
                allocation_set=alloc_set, conflict_type=ConflictType.THRESHOLD_BREACH
            ).delete()
            return self._detect_threshold_breach(
                alloc_set.version, alloc_set, alloc_set.engine_job
            )

    # ------------------------------------------------------------------ #
    # 1. CAPACITY_EXCEEDED — any member/sprint where allocated engine days
    #    exceed MemberCapacity.net_capacity.
    # ------------------------------------------------------------------ #

    @staticmethod
    def _detect_capacity_exceeded(
        version: PlanVersion, alloc_set: AllocationSet, job: EngineJob
    ) -> list[Conflict]:
        capacity_map = {
            (mc.member_id, mc.sprint_id): mc.net_capacity
            for mc in selectors.get_member_capacities_for_version(version)
        }
        grouped = (
            Allocation.objects.filter(allocation_set=alloc_set, member__isnull=False)
            .values("member_id", "sprint_id")
            .annotate(total_days=Sum("engine_days"))
        )

        created: list[Conflict] = []
        for row in grouped:
            capacity = capacity_map.get((row["member_id"], row["sprint_id"]))
            if capacity is None or row["total_days"] <= capacity:
                continue

            sample = (
                Allocation.objects.filter(
                    allocation_set=alloc_set,
                    member_id=row["member_id"],
                    sprint_id=row["sprint_id"],
                )
                .select_related("project", "team", "phase", "member", "sprint")
                .first()
            )
            description = (
                f"{sample.member} is allocated {row['total_days']} day(s) in "
                f"{sample.sprint} but capacity is only {capacity} day(s)."
                if sample
                else "Allocated days exceed member capacity."
            )
            created.append(
                Conflict.objects.create(
                    allocation_set=alloc_set,
                    engine_job=job,
                    conflict_type=ConflictType.CAPACITY_EXCEEDED,
                    severity=ConflictSeverity.ERROR,
                    affected_project=sample.project if sample else None,
                    affected_phase=sample.phase if sample else None,
                    affected_member_id=row["member_id"],
                    affected_sprint_id=row["sprint_id"],
                    affected_team=sample.team if sample else None,
                    description=description,
                    engine_data={
                        "allocated_days": str(row["total_days"]),
                        "capacity_days": str(capacity),
                        "excess_days": str(row["total_days"] - capacity),
                    },
                )
            )
        return created

    # ------------------------------------------------------------------ #
    # 2. THRESHOLD_BREACH — per project, total allocated days (respecting
    #    Allocation.override_days) vs. required days, flagged when the
    #    percentage difference exceeds PlanVersion.threshold_percentage.
    # ------------------------------------------------------------------ #

    @staticmethod
    def _detect_threshold_breach(
        version: PlanVersion, alloc_set: AllocationSet, job: EngineJob | None
    ) -> list[Conflict]:
        threshold = version.threshold_percentage or Decimal("0")

        created: list[Conflict] = []
        for plan_project in selectors.get_configured_projects(version):
            teams = version_team_selectors.get_teams_for_plan_project(plan_project)
            team_days_sum = sum((t.allocated_days for t in teams), Decimal("0"))
            required_days = (
                team_days_sum if team_days_sum else plan_project.days_required
            )
            if not required_days:
                continue

            allocations = Allocation.objects.filter(
                allocation_set=alloc_set, project=plan_project.project
            )
            total_allocated = sum((a.effective_days for a in allocations), Decimal("0"))

            diff_pct = (
                abs(total_allocated - required_days) / required_days * Decimal("100")
            )
            if diff_pct <= threshold:
                continue

            created.append(
                Conflict.objects.create(
                    allocation_set=alloc_set,
                    engine_job=job,
                    conflict_type=ConflictType.THRESHOLD_BREACH,
                    severity=ConflictSeverity.WARNING,
                    affected_project=plan_project.project,
                    description=(
                        f"{plan_project.project} is allocated {total_allocated} "
                        f"day(s) against a required {required_days} day(s) "
                        f"({diff_pct:.2f}% difference, threshold {threshold}%)."
                    ),
                    engine_data={
                        "allocated_days": str(total_allocated),
                        "required_days": str(required_days),
                        "diff_percentage": str(diff_pct),
                    },
                )
            )
        return created

    # ------------------------------------------------------------------ #
    # 3. TIMELINE_BREACH — any phase with assignments configured but zero
    #    Allocation rows produced.
    # ------------------------------------------------------------------ #

    @staticmethod
    def _detect_timeline_breach(
        version: PlanVersion, alloc_set: AllocationSet, job: EngineJob
    ) -> list[Conflict]:
        created: list[Conflict] = []
        # Walked project-by-project, matching #181's "never bulk-query
        # everything and cross-reference in memory" instruction.
        for plan_project in selectors.get_configured_projects(version):
            for plan_version_team in version_team_selectors.get_teams_for_plan_project(
                plan_project
            ):
                for phase in phase_selectors.get_phases_for_plan_project_team(
                    plan_version_team
                ):
                    if not selectors.get_assignments_for_phase(phase).exists():
                        continue
                    if Allocation.objects.filter(
                        allocation_set=alloc_set, phase=phase
                    ).exists():
                        continue

                    created.append(
                        Conflict.objects.create(
                            allocation_set=alloc_set,
                            engine_job=job,
                            conflict_type=ConflictType.TIMELINE_BREACH,
                            severity=ConflictSeverity.ERROR,
                            affected_project=plan_project.project,
                            affected_phase=phase,
                            affected_team=plan_version_team.team,
                            description=(
                                f"{phase} has assignments but produced no "
                                "allocations — its sprint window may be fully "
                                "expired or paused."
                            ),
                            engine_data={"phase_code": phase.code},
                        )
                    )
        return created

    # ------------------------------------------------------------------ #
    # 4. UNRESOLVABLE_GAP — any PlaceholderEngineer slot that received
    #    allocation, one Conflict + one auto-created ManpowerRequest per slot.
    # ------------------------------------------------------------------ #

    @staticmethod
    def _detect_unresolvable_gap(
        alloc_set: AllocationSet, job: EngineJob
    ) -> list[Conflict]:
        placeholder_ids = (
            Allocation.objects.filter(
                allocation_set=alloc_set, placeholder_engineer__isnull=False
            )
            .values_list("placeholder_engineer_id", flat=True)
            .distinct()
        )

        created: list[Conflict] = []
        for placeholder_id in placeholder_ids:
            placeholder = PlaceholderEngineer.objects.select_related(
                "team", "phase"
            ).get(id=placeholder_id)
            rows = list(
                Allocation.objects.filter(
                    allocation_set=alloc_set, placeholder_engineer=placeholder
                ).select_related("sprint", "project")
            )
            if not rows:
                continue

            total_days = sum((r.engine_days for r in rows), Decimal("0"))
            sprint_ids = {r.sprint_id for r in rows}
            earliest_row = min(rows, key=lambda r: r.sprint.sprint_number)

            conflict = Conflict.objects.create(
                allocation_set=alloc_set,
                engine_job=job,
                conflict_type=ConflictType.UNRESOLVABLE_GAP,
                severity=ConflictSeverity.ERROR,
                affected_project=earliest_row.project,
                affected_phase=placeholder.phase,
                affected_team=placeholder.team,
                affected_sprint=earliest_row.sprint,
                description=(
                    f"No engineer available for {placeholder.name}; earliest "
                    f"need is {earliest_row.sprint}."
                ),
                engine_data={
                    "placeholder_engineer_code": placeholder.code,
                    "total_days": str(total_days),
                    "sprint_count": len(sprint_ids),
                },
            )
            created.append(conflict)

            ManpowerRequest.objects.create(
                allocation_set=alloc_set,
                conflict=conflict,
                team=placeholder.team,
                phase=placeholder.phase,
                sprints_needed=len(sprint_ids),
                days_needed=total_days,
            )
        return created
