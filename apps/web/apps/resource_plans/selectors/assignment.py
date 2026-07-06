from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import PlanAssignment, PlanPhase


def get_assignments_for_phase(phase: PlanPhase) -> QuerySet[PlanAssignment]:
    return PlanAssignment.objects.filter(phase=phase).select_related(
        "member",
        "member__profile",
        "replaces_member",
        "replaces_member__profile",
    )


def get_assignment_by_code(code: str) -> PlanAssignment | None:
    try:
        return PlanAssignment.objects.select_related(
            "phase",
            "phase__plan_project_team",
            "phase__plan_project_team__plan_project",
            "phase__plan_project_team__plan_project__version",
            "phase__plan_project_team__plan_project__version__plan",
            "member",
            "member__profile",
            "replaces_member",
            "replaces_member__profile",
        ).get(code=code)
    except PlanAssignment.DoesNotExist:
        return None
