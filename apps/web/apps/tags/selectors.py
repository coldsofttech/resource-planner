from django.db.models import Count, QuerySet

from apps.tags.models import Tag


def _normalise(name: str) -> str:
    n = name.strip().lower()
    return n if n.startswith("#") else f"#{n}"


def get_all_tags() -> QuerySet[Tag]:
    return Tag.objects.select_related("created_by", "updated_by").all()


def get_tag_by_code(code: str) -> Tag | None:
    try:
        return Tag.objects.select_related("created_by", "updated_by").get(code=code)
    except Tag.DoesNotExist:
        return None


def get_tag_by_name(name: str) -> Tag | None:
    try:
        return Tag.objects.select_related("created_by", "updated_by").get(
            name__iexact=name.strip()
        )
    except Tag.DoesNotExist:
        return None


def tag_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = Tag.objects.filter(name=_normalise(name))
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_tag_stats() -> dict:
    return Tag.objects.aggregate(total=Count("id"))
