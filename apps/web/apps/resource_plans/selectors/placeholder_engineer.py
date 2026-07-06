from __future__ import annotations

from django.db.models import QuerySet

from apps.resource_plans.models import PlaceholderEngineer, PlanVersion
from apps.teams.models import Team


def get_placeholder_engineers_for_team(
    version: PlanVersion, team: Team
) -> QuerySet[PlaceholderEngineer]:
    return PlaceholderEngineer.objects.filter(version=version, team=team).order_by(
        "slot_number"
    )
