from __future__ import annotations

from apps.core.exceptions import ValidationException
from apps.resource_plans.constants import Confidence, DependencyType, Priority
from apps.resource_plans.models import PlanPhase, PlanVersionProject


class DependencyGraphService:
    """Pure graph logic over PlanPhaseDependency — no persistence of its own."""

    _PRIORITY_WEIGHT = {
        str(Priority.VERY_HIGH): 0,
        str(Priority.HIGH): 1,
        str(Priority.MEDIUM): 2,
        str(Priority.LOW): 3,
    }
    _CONFIDENCE_WEIGHT = {
        str(Confidence.VERY_HIGH): 0,
        str(Confidence.HIGH): 1,
        str(Confidence.MEDIUM): 2,
        str(Confidence.LOW): 3,
    }
    _UNSET_WEIGHT = 4

    @classmethod
    def _tie_break_key(
        cls,
        phase: PlanPhase,
        proj_by_phase_id: dict[int, PlanVersionProject],
    ) -> tuple:
        project = proj_by_phase_id.get(phase.id)
        dates_strict = 0 if (project is not None and project.dates_strict) else 1
        effective_priority = project.effective_priority if project else None
        priority = (
            cls._PRIORITY_WEIGHT.get(effective_priority, cls._UNSET_WEIGHT)
            if effective_priority is not None
            else cls._UNSET_WEIGHT
        )
        effective_confidence = project.effective_confidence if project else None
        confidence = (
            cls._CONFIDENCE_WEIGHT.get(effective_confidence, cls._UNSET_WEIGHT)
            if effective_confidence is not None
            else cls._UNSET_WEIGHT
        )
        end_sprint_number = (
            phase.end_sprint.sprint_number if phase.end_sprint_id else float("inf")
        )
        # No dedicated display-order field exists on PlanVersionProject —
        # its creation-order id is used as a stable, deterministic proxy.
        project_display_order = project.id if project else float("inf")
        return (
            dates_strict,
            priority,
            confidence,
            end_sprint_number,
            project_display_order,
            phase.sequence_order,
        )

    @classmethod
    def topological_sort(
        cls,
        phases: list[PlanPhase],
        proj_by_phase_id: dict[int, PlanVersionProject],
    ) -> list[PlanPhase]:
        phase_by_id = {phase.id: phase for phase in phases}
        scoped_ids = set(phase_by_id.keys())

        # Defensive: PlanPhaseDependency has no DB-level guarantee that
        # predecessor_phase belongs to the same plan version (see #185) —
        # only count edges where both ends are within the given phase set.
        dependents: dict[int, list[int]] = {pid: [] for pid in scoped_ids}
        in_degree: dict[int, int] = {pid: 0 for pid in scoped_ids}
        for phase in phases:
            for dep in phase.dependencies.all():
                if dep.predecessor_phase_id not in scoped_ids:
                    continue
                in_degree[phase.id] += 1
                dependents[dep.predecessor_phase_id].append(phase.id)

        frontier = [pid for pid, deg in in_degree.items() if deg == 0]
        ordered: list[PlanPhase] = []

        while frontier:
            frontier.sort(
                key=lambda pid: cls._tie_break_key(phase_by_id[pid], proj_by_phase_id)
            )
            next_id = frontier.pop(0)
            ordered.append(phase_by_id[next_id])
            for dependent_id in dependents[next_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    frontier.append(dependent_id)

        if len(ordered) != len(phases):
            raise ValidationException(
                "Circular dependency detected among plan phases — cannot "
                "compute a topological order."
            )
        return ordered

    @staticmethod
    def earliest_start(
        phase: PlanPhase,
        completed: dict[int, tuple[int, int]],
        sprint_nums: list[int] | None,
    ) -> int | None:
        constraints = []
        for dep in phase.dependencies.all():
            if dep.predecessor_phase_id not in completed:
                continue
            pred_start, pred_end = completed[dep.predecessor_phase_id]
            if dep.dependency_type == DependencyType.FINISH_TO_START:
                constraints.append(pred_end + 1 + dep.lag_sprints)
            elif dep.dependency_type == DependencyType.START_TO_START:
                constraints.append(pred_start + dep.lag_sprints)
            # FINISH_TO_FINISH / START_TO_FINISH constrain the phase's END,
            # not its START — modeling that requires phase duration, which
            # isn't available at this point in the pipeline. They impose no
            # additional start-time constraint here; a full implementation
            # is deferred to a future issue.

        if not constraints:
            return None

        earliest = max(constraints)
        if sprint_nums:
            candidates = [n for n in sprint_nums if n >= earliest]
            if candidates:
                return min(candidates)
            return max(sprint_nums)
        return earliest
