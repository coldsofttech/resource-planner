from django.contrib.auth.models import Group
from django.db.models import Q, QuerySet

from apps.permissions.constants import PermissionScope
from apps.permissions.models import (
    GroupPermissionCategory,
    PermissionCategory,
    UserPermissionCategory,
)
from apps.users.models import GroupProfile, User, UserProfile


def get_all_categories(*, module: str | None = None) -> QuerySet[PermissionCategory]:
    """Returns the base PermissionCategory queryset, optionally filtered by module."""
    qs = PermissionCategory.objects.all()
    if module:
        qs = qs.filter(module=module)
    return qs


def get_category_by_code(code: str) -> PermissionCategory | None:
    """Returns a single PermissionCategory with permissions prefetched, or None."""
    try:
        return PermissionCategory.objects.prefetch_related("permissions").get(code=code)
    except PermissionCategory.DoesNotExist:
        return None


def get_user_by_profile_code(code: str) -> User | None:
    """Resolves a UserProfile code (e.g. USER-1) to the underlying User."""
    try:
        return UserProfile.objects.select_related("user").get(code=code).user
    except UserProfile.DoesNotExist:
        return None


def get_user_assignment_by_code(code: str) -> UserPermissionCategory | None:
    """Returns a single UserPermissionCategory by its code, or None."""
    try:
        return UserPermissionCategory.objects.select_related("user", "category").get(
            code=code
        )
    except UserPermissionCategory.DoesNotExist:
        return None


def get_user_categories(user: User) -> QuerySet[UserPermissionCategory]:
    """Returns all permission category assignments for a user."""
    return (
        UserPermissionCategory.objects.select_related("category")
        .filter(user=user)
        .order_by("category__module", "category__order")
    )


def get_effective_user_assignments(user: User) -> list[dict]:
    """
    Returns the union of group and direct permission category assignments for a
    user, with the effective (highest) scope per category and a 'via' indicator.
    Results are sorted by module then category order.
    """
    group_map: dict[int, dict] = {}
    for ga in GroupPermissionCategory.objects.filter(group__user=user).select_related(
        "category"
    ):
        cat_id = ga.category_id
        if cat_id not in group_map or ga.scope > group_map[cat_id]["scope"]:
            group_map[cat_id] = {"category": ga.category, "scope": ga.scope}

    direct_map: dict[int, dict] = {}
    for ua in UserPermissionCategory.objects.filter(user=user).select_related(
        "category"
    ):
        direct_map[ua.category_id] = {"category": ua.category, "scope": ua.scope}

    results = []
    for cat_id in set(group_map) | set(direct_map):
        g = group_map.get(cat_id)
        d = direct_map.get(cat_id)

        if g and d:
            via = "both"
            scope = max(g["scope"], d["scope"])
            category = g["category"]
        elif g:
            via = "group"
            scope = g["scope"]
            category = g["category"]
        else:
            assert d is not None
            via = "direct"
            scope = d["scope"]
            category = d["category"]

        results.append({"category": category, "scope": scope, "via": via})

    return sorted(results, key=lambda x: (x["category"].module, x["category"].order))


def get_user_permissions(user: User) -> set[str]:
    """
    Returns the flat set of resolved permission strings for a user.
    Traverses both group and direct category assignments.
    Used by the custom auth backend for has_perm() checks.
    """
    from django.contrib.auth.models import Permission

    perms = (
        Permission.objects.filter(
            Q(categories__group_assignments__group__user=user)
            | Q(categories__user_assignments__user=user)
        )
        .values_list("content_type__app_label", "codename")
        .distinct()
    )
    return {f"{app}.{code}" for app, code in perms}


def get_group_by_profile_code(code: str) -> Group | None:
    """Resolves a GroupProfile code (e.g. USRGRP-1) to the underlying auth.Group."""
    try:
        return GroupProfile.objects.select_related("group").get(code=code).group
    except GroupProfile.DoesNotExist:
        return None


def get_group_assignment_by_code(code: str) -> GroupPermissionCategory | None:
    """Returns a single GroupPermissionCategory by its code, or None."""
    try:
        return GroupPermissionCategory.objects.select_related("group", "category").get(
            code=code
        )
    except GroupPermissionCategory.DoesNotExist:
        return None


def get_group_categories(group: Group) -> QuerySet[GroupPermissionCategory]:
    """Returns all permission category assignments for a group."""
    return (
        GroupPermissionCategory.objects.select_related("category")
        .filter(group=group)
        .order_by("category__module", "category__order")
    )


def get_effective_scope(user: User, module: str, codename: str) -> PermissionScope:
    """
    Returns the broadest scope the user holds for a given module + codename.
    Resolves across both group and direct assignments — highest value wins.
    """
    group_scopes = GroupPermissionCategory.objects.filter(
        group__user=user,
        category__module=module,
        category__codename=codename,
    ).values_list("scope", flat=True)

    user_scopes = UserPermissionCategory.objects.filter(
        user=user,
        category__module=module,
        category__codename=codename,
    ).values_list("scope", flat=True)

    all_scopes = [*group_scopes, *user_scopes]

    if not all_scopes:
        return PermissionScope.NONE  # type: ignore[return-value]

    return PermissionScope(max(all_scopes))  # type: ignore[return-value]
