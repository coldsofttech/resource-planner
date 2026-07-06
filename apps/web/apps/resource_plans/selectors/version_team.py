from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import PlanVersion, PlanVersionProject, PlanVersionTeam
from apps.teams.models import Team


def get_teams_for_plan_project(
    plan_project: PlanVersionProject,
) -> QuerySet[PlanVersionTeam]:
    return (
        PlanVersionTeam.objects.filter(plan_project=plan_project)
        .select_related("team")
        .order_by("sequence_order", "team__name")
    )


def get_version_team_by_code(code: str) -> PlanVersionTeam | None:
    try:
        return PlanVersionTeam.objects.select_related(
            "plan_project",
            "plan_project__version",
            "plan_project__version__plan",
            "team",
        ).get(code=code)
    except PlanVersionTeam.DoesNotExist:
        return None


def version_team_exists(plan_project: PlanVersionProject, team: Team) -> bool:
    return PlanVersionTeam.objects.filter(plan_project=plan_project, team=team).exists()


def get_teams_for_version(version: PlanVersion) -> QuerySet[Team]:
    return Team.objects.filter(
        resource_plan_versions__plan_project__version=version
    ).distinct()
