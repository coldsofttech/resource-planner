from django.db.models import Count, Q, QuerySet

from apps.roles.models import Role


def get_all_roles() -> QuerySet[Role]:
    return Role.objects.select_related("created_by", "updated_by").all()


def get_active_roles() -> QuerySet[Role]:
    return Role.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_role_by_code(code: str) -> Role | None:
    try:
        return Role.objects.select_related("created_by", "updated_by").get(code=code)
    except Role.DoesNotExist:
        return None


def role_exists(role: str, exclude_pk: int | None = None) -> bool:
    qs = Role.objects.filter(role=role)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_role_options() -> QuerySet[Role]:
    return (
        Role.objects.filter(is_active=True)
        .only("code", "role", "is_default", "is_assignable", "is_leadership")
        .order_by("role")
    )


def get_role_stats() -> dict:
    return Role.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
