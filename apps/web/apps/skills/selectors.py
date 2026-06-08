from django.db.models import Count, Q, QuerySet

from apps.skills.models import Skill


def get_all_skills() -> QuerySet[Skill]:
    return Skill.objects.select_related("created_by", "updated_by").all()


def get_active_skills() -> QuerySet[Skill]:
    return Skill.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_skill_by_code(code: str) -> Skill | None:
    try:
        return Skill.objects.select_related("created_by", "updated_by").get(code=code)
    except Skill.DoesNotExist:
        return None


def skill_exists(skill: str, exclude_pk: int | None = None) -> bool:
    qs = Skill.objects.filter(skill=skill)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_skill_options() -> QuerySet[Skill]:
    return Skill.objects.filter(is_active=True).only("code", "skill").order_by("skill")


def get_skill_stats() -> dict:
    return Skill.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
