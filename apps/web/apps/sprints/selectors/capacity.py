from __future__ import annotations

from django.db.models import QuerySet

from apps.sprints.models import Capacity, Sprint
from apps.users.models import User


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


def get_capacity_for_member_sprint(member: User, sprint: Sprint) -> Capacity | None:
    try:
        return Capacity.objects.get(member=member, sprint=sprint)
    except Capacity.DoesNotExist:
        return None


def get_capacity_by_ids(member_id: int, sprint_id: int) -> Capacity | None:
    try:
        return Capacity.objects.get(member_id=member_id, sprint_id=sprint_id)
    except Capacity.DoesNotExist:
        return None
