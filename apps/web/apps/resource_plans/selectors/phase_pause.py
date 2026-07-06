from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import PlanPhase, PlanPhasePause
from apps.sprints.models import Sprint


def get_pauses_for_phase(phase: PlanPhase) -> QuerySet[PlanPhasePause]:
    return (
        PlanPhasePause.objects.filter(phase=phase)
        .select_related("pause_from", "pause_until_sprint", "resume_sprint")
        .order_by("pause_from__sprint_number")
    )


def get_pause_by_code(code: str) -> PlanPhasePause | None:
    try:
        return PlanPhasePause.objects.select_related(
            "phase",
            "phase__plan_project_team",
            "phase__plan_project_team__plan_project",
            "phase__plan_project_team__plan_project__version",
            "phase__plan_project_team__plan_project__version__plan",
            "pause_from",
            "pause_until_sprint",
            "resume_sprint",
        ).get(code=code)
    except PlanPhasePause.DoesNotExist:
        return None


def pause_from_exists(
    phase: PlanPhase, pause_from: Sprint, exclude_pk: int | None = None
) -> bool:
    qs = PlanPhasePause.objects.filter(phase=phase, pause_from=pause_from)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
