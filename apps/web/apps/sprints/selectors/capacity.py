from __future__ import annotations

from django.db.models import QuerySet

from apps.sprints.models import Capacity, Sprint


def get_capacity_for_sprint(sprint: Sprint) -> QuerySet[Capacity]:
    return (
        Capacity.objects.filter(sprint=sprint)
        .select_related(
            "member",
            "member__profile",
            "member__profile__location",
        )
        .prefetch_related("member__team_assignments__team")
        .order_by("member__first_name", "member__last_name")
    )
