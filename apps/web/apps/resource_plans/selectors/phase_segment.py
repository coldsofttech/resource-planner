from __future__ import annotations

from django.db.models import Max, QuerySet

from apps.resource_plans.models import PlanPhase, PlanPhaseSegment


def get_segments_for_phase(phase: PlanPhase) -> QuerySet[PlanPhaseSegment]:
    return PlanPhaseSegment.objects.filter(phase=phase).order_by("segment_order")


def get_segment_by_code(code: str) -> PlanPhaseSegment | None:
    try:
        return PlanPhaseSegment.objects.select_related(
            "phase",
            "phase__plan_project_team",
            "phase__plan_project_team__plan_project",
            "phase__plan_project_team__plan_project__version",
            "phase__plan_project_team__plan_project__version__plan",
        ).get(code=code)
    except PlanPhaseSegment.DoesNotExist:
        return None


def get_next_segment_order(phase: PlanPhase) -> int:
    result = PlanPhaseSegment.objects.filter(phase=phase).aggregate(
        max_order=Max("segment_order")
    )
    return (result["max_order"] or 0) + 1
