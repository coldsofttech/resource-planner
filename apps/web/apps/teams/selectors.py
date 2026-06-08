from django.db.models import Count, Q, QuerySet

from apps.teams.models import Team


def get_all_teams() -> QuerySet[Team]:
    return Team.objects.select_related("created_by", "updated_by").all()


def get_active_teams() -> QuerySet[Team]:
    return Team.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_team_by_code(code: str) -> Team | None:
    try:
        return Team.objects.select_related("created_by", "updated_by").get(code=code)
    except Team.DoesNotExist:
        return None


def team_name_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = Team.objects.filter(name=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_team_stats() -> dict:
    return Team.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
