from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import PlanPhase, PlanVersionTeam


def get_phases_for_plan_project_team(
    plan_project_team: PlanVersionTeam,
) -> QuerySet[PlanPhase]:
    return (
        PlanPhase.objects.filter(plan_project_team=plan_project_team)
        .select_related("start_sprint", "end_sprint")
        .order_by("sequence_order")
    )


def get_phase_by_code(code: str) -> PlanPhase | None:
    try:
        return PlanPhase.objects.select_related(
            "plan_project_team",
            "plan_project_team__plan_project",
            "plan_project_team__plan_project__version",
            "plan_project_team__plan_project__version__plan",
            "start_sprint",
            "end_sprint",
        ).get(code=code)
    except PlanPhase.DoesNotExist:
        return None


def phase_name_exists(
    plan_project_team: PlanVersionTeam, name: str, exclude_pk: int | None = None
) -> bool:
    qs = PlanPhase.objects.filter(plan_project_team=plan_project_team, name=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
