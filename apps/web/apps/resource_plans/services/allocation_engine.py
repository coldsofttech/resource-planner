from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Max

from apps.resource_plans import selectors
from apps.resource_plans.constants import AssignmentType, SplitMode
from apps.resource_plans.models import (
    Allocation,
    AllocationSet,
    EngineJob,
    PlaceholderEngineer,
    PlanAssignment,
    PlanPhase,
    PlanVersion,
    PlanVersionProject,
    PlanVersionTeam,
)
from apps.resource_plans.selectors import phase as phase_selectors
from apps.resource_plans.selectors import phase_segment as phase_segment_selectors
from apps.resource_plans.selectors import version_team as version_team_selectors
from apps.resource_plans.services.dependency_graph import DependencyGraphService
from apps.resource_plans.services.ramp_distribution import RampDistributionService
from apps.sprints.models import Sprint
from apps.teams import selectors as team_selectors
from apps.teams.models import Team
from apps.users.models import User


class AllocationEngineService:
    """Backs Engine Step 6 (Compute Allocations) — creates an AllocationSet
    and populates Allocation rows for a version, in topological phase order.
    """

    def run(self, job: EngineJob) -> AllocationSet:
        version = job.version
        fy = job.plan.financial_year
        sprints_in_fy = list(Sprint.objects.filter(financial_year=fy))
        sprint_by_number = {s.sprint_number: s for s in sprints_in_fy}
        sprint_nums = sorted(sprint_by_number.keys())
        fy_min = sprint_nums[0] if sprint_nums else None
        fy_max = sprint_nums[-1] if sprint_nums else None

        allocation_set = AllocationSet.objects.create(version=version, engine_job=job)

        remaining_capacity = {
            (mc.member_id, mc.sprint_id): mc.net_capacity
            for mc in selectors.get_member_capacities_for_version(version)
        }
        member_load: dict[int, Decimal] = {}

        # Phases are collected project-by-project (avoids one flat
        # cross-project query and keeps memory bounded per #181's "never
        # bulk-process everything in memory across projects" instruction),
        # but the actual processing order below is the GLOBAL topological
        # order from DependencyGraphService — dependency correctness has
        # to win over a strict per-project iteration, since a phase can
        # depend on a phase in a different project/team (see
        # PlanPhaseDependency's own docstring).
        phases: list[PlanPhase] = []
        proj_by_phase_id: dict[int, PlanVersionProject] = {}
        for plan_project in selectors.get_configured_projects(version):
            for plan_version_team in version_team_selectors.get_teams_for_plan_project(
                plan_project
            ):
                for phase in phase_selectors.get_phases_for_plan_project_team(
                    plan_version_team
                ):
                    phases.append(phase)
                    proj_by_phase_id[phase.id] = plan_project

        ordered_phases = DependencyGraphService.topological_sort(
            phases, proj_by_phase_id
        )

        completed: dict[int, tuple[int, int]] = {}

        with transaction.atomic():
            for phase in ordered_phases:
                window = self._compute_active_window(
                    phase, completed, sprint_nums, fy_min, fy_max
                )
                if window is None:
                    continue
                start_num, end_num = window
                completed[phase.id] = (start_num, end_num)

                active_numbers = self._exclude_paused(phase, start_num, end_num)
                active_sprints = [
                    sprint_by_number[n] for n in active_numbers if n in sprint_by_number
                ]
                if not active_sprints:
                    continue

                plan_version_team = phase.plan_project_team
                plan_project = proj_by_phase_id[phase.id]
                project = plan_project.project
                team = plan_version_team.team

                total_effort = self._phase_effort(phase, plan_version_team)
                assignments = list(selectors.get_assignments_for_phase(phase))
                is_synthetic = not assignments
                if is_synthetic:
                    assignments = [None]

                shares = self._effort_shares(phase, assignments, total_effort)
                segments = list(phase_segment_selectors.get_segments_for_phase(phase))

                zipped_assignments = zip(assignments, shares, strict=True)
                for assignment, assignment_days in zipped_assignments:
                    resolved = self._resolve_assignee(
                        assignment, team, phase, active_sprints, member_load, version
                    )
                    member, placeholder_engineer = resolved[0], resolved[1]
                    assignment_type, includes_in_budget = resolved[2], resolved[3]

                    distributed = RampDistributionService.distribute(
                        assignment_days,
                        len(active_sprints),
                        phase.ramp_pattern,
                        segments,
                        phase.max_days_per_sprint,
                    )

                    for sprint, days in zip(active_sprints, distributed, strict=True):
                        if member is not None:
                            key = (member.id, sprint.id)
                            cap = remaining_capacity.get(key)
                            if cap is not None:
                                days = min(days, max(cap, Decimal("0")))
                                remaining_capacity[key] = cap - days
                            member_load[member.id] = (
                                member_load.get(member.id, Decimal("0")) + days
                            )

                        # Allocation extends CodeModel, whose `code` field is
                        # only populated inside an overridden save() —
                        # bulk_create() would leave every row's code blank
                        # and collide on its unique constraint (see #186).
                        # Individual create() calls are required.
                        Allocation.objects.create(
                            allocation_set=allocation_set,
                            programme=project.programme,
                            project=project,
                            team=team,
                            member=member,
                            placeholder_engineer=placeholder_engineer,
                            sprint=sprint,
                            phase=phase,
                            assignment=assignment,
                            assignment_type=assignment_type,
                            includes_in_budget=includes_in_budget,
                            engine_days=days,
                        )

        return allocation_set

    @staticmethod
    def _compute_active_window(
        phase: PlanPhase,
        completed: dict[int, tuple[int, int]],
        sprint_nums: list[int],
        fy_min: int | None,
        fy_max: int | None,
    ) -> tuple[int, int] | None:
        earliest = DependencyGraphService.earliest_start(phase, completed, sprint_nums)
        start_num = earliest
        if phase.start_sprint_id:
            phase_start = phase.start_sprint.sprint_number
            start_num = (
                max(start_num, phase_start) if start_num is not None else phase_start
            )
        if start_num is None:
            start_num = fy_min

        end_num = phase.end_sprint.sprint_number if phase.end_sprint_id else fy_max

        if fy_min is not None and start_num is not None:
            start_num = max(start_num, fy_min)
        if fy_max is not None and end_num is not None:
            end_num = min(end_num, fy_max)

        if start_num is None or end_num is None or start_num > end_num:
            return None
        return (start_num, end_num)

    @staticmethod
    def _exclude_paused(phase: PlanPhase, start_num: int, end_num: int) -> list[int]:
        excluded: set[int] = set()
        for pause in selectors.get_pauses_for_phase(phase):
            pause_start = pause.pause_from.sprint_number
            pause_end = pause.resume_sprint.sprint_number - 1
            lo = max(pause_start, start_num)
            hi = min(pause_end, end_num)
            excluded.update(range(lo, hi + 1))
        return [n for n in range(start_num, end_num + 1) if n not in excluded]

    @staticmethod
    def _phase_effort(phase: PlanPhase, plan_version_team: PlanVersionTeam) -> Decimal:
        if phase.days_effort and phase.days_effort > 0:
            return phase.days_effort
        phase_count = PlanPhase.objects.filter(
            plan_project_team=plan_version_team
        ).count()
        if phase_count == 0:
            return Decimal("0")
        return plan_version_team.allocated_days / phase_count

    @staticmethod
    def _effort_shares(
        phase: PlanPhase,
        assignments: list[PlanAssignment | None],
        total_effort: Decimal,
    ) -> list[Decimal]:
        if phase.split_mode == SplitMode.PERCENT:
            shares = []
            for a in assignments:
                if a is None:
                    shares.append(total_effort)
                else:
                    pct = a.split_value or Decimal("0")
                    shares.append(total_effort * pct / Decimal("100"))
            return shares
        if phase.split_mode == SplitMode.DAYS:
            return [
                a.split_value
                if (a is not None and a.split_value is not None)
                else total_effort
                for a in assignments
            ]
        # EQUAL / AUTO — an even split across however many assignments (or
        # the single synthetic slot) exist on the phase.
        n = len(assignments)
        return [total_effort / n for _ in assignments] if n else []

    @classmethod
    def _resolve_assignee(
        cls,
        assignment: PlanAssignment | None,
        team: Team,
        phase: PlanPhase,
        active_sprints: list[Sprint],
        member_load: dict[int, Decimal],
        version: PlanVersion,
    ) -> tuple[User | None, PlaceholderEngineer | None, str, bool]:
        if assignment is not None and not assignment.auto_assign:
            return (
                assignment.member,
                None,
                assignment.assignment_type,
                assignment.includes_in_budget,
            )

        assignment_type = (
            assignment.assignment_type if assignment else str(AssignmentType.ENGINEER)
        )
        includes_in_budget = assignment.includes_in_budget if assignment else True

        candidates = list(team_selectors.get_active_members_for_team(team))
        if candidates:
            best = min(candidates, key=lambda m: member_load.get(m.id, Decimal("0")))
            return best, None, assignment_type, includes_in_budget

        placeholder = cls._get_or_create_placeholder(
            version, team, phase, active_sprints
        )
        return None, placeholder, assignment_type, includes_in_budget

    @staticmethod
    def _get_or_create_placeholder(
        version: PlanVersion, team: Team, phase: PlanPhase, active_sprints: list[Sprint]
    ) -> PlaceholderEngineer:
        active_sprint_ids = {s.id for s in active_sprints}
        existing = selectors.get_placeholder_engineers_for_team(version, team)
        for placeholder in existing:
            # Reuse spans the whole plan version, not just this engine
            # run — a placeholder's commitments persist across runs, so
            # every prior Allocation against it (any AllocationSet) counts
            # toward whether its sprints are already "busy."
            busy_sprint_ids = set(
                Allocation.objects.filter(placeholder_engineer=placeholder).values_list(
                    "sprint_id", flat=True
                )
            )
            if not (busy_sprint_ids & active_sprint_ids):
                return placeholder

        next_slot = (
            existing.aggregate(max_slot=Max("slot_number"))["max_slot"] or 0
        ) + 1
        return PlaceholderEngineer.objects.create(
            version=version, team=team, phase=phase, slot_number=next_slot
        )
