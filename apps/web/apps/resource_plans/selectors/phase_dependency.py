from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import PlanPhase, PlanPhaseDependency, PlanVersion


def get_dependencies_for_phase(phase: PlanPhase) -> QuerySet[PlanPhaseDependency]:
    return PlanPhaseDependency.objects.filter(phase=phase).select_related(
        "predecessor_phase",
        "predecessor_phase__plan_project_team",
        "predecessor_phase__plan_project_team__team",
        "predecessor_phase__plan_project_team__plan_project",
        "predecessor_phase__plan_project_team__plan_project__project",
    )


def get_dependency_by_code(code: str) -> PlanPhaseDependency | None:
    try:
        return PlanPhaseDependency.objects.select_related(
            "phase",
            "phase__plan_project_team",
            "phase__plan_project_team__plan_project",
            "phase__plan_project_team__plan_project__version",
            "phase__plan_project_team__plan_project__version__plan",
            "predecessor_phase",
        ).get(code=code)
    except PlanPhaseDependency.DoesNotExist:
        return None


def dependency_exists(
    phase: PlanPhase, predecessor_phase: PlanPhase, exclude_pk: int | None = None
) -> bool:
    qs = PlanPhaseDependency.objects.filter(
        phase=phase, predecessor_phase=predecessor_phase
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_available_predecessor_phases(
    version: PlanVersion, exclude_phase: PlanPhase
) -> QuerySet[PlanPhase]:
    return (
        PlanPhase.objects.filter(plan_project_team__plan_project__version=version)
        .exclude(pk=exclude_phase.pk)
        .select_related(
            "plan_project_team__team",
            "plan_project_team__plan_project__project",
        )
        .order_by(
            "plan_project_team__plan_project__project__name",
            "plan_project_team__team__name",
            "name",
        )
    )
