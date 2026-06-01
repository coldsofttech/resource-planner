from apps.permissions.constants import PermissionScope
from apps.permissions.selectors import get_user_permissions


class PermissionCategoryBackend:
    """
    Custom auth backend that resolves permissions through PermissionCategory
    assignments rather than Django's default group/user permission M2M tables.

    Register in settings.py:
        AUTHENTICATION_BACKENDS = [
            "apps.permissions.backends.PermissionCategoryBackend",
            "django.contrib.auth.backends.ModelBackend",
        ]
    ModelBackend is kept as a fallback for superuser checks only.
    """

    def authenticate(self, request, **kwargs):
        return None

    def _get_permissions(self, user_obj) -> set[str]:
        if not hasattr(user_obj, "_category_perm_cache"):
            user_obj._category_perm_cache = get_user_permissions(user_obj)
        return user_obj._category_perm_cache

    def get_all_permissions(self, user_obj, obj=None) -> set[str]:
        if not user_obj.is_active or user_obj.is_anonymous:
            return set()
        return self._get_permissions(user_obj)

    def has_perm(self, user_obj, perm, obj=None) -> bool:
        if not user_obj.is_active or user_obj.is_anonymous:
            return False
        if user_obj.is_superuser:
            return True
        if perm not in self.get_all_permissions(user_obj):
            return False
        if obj is None:
            return True
        return self._scope_covers_object(
            user_obj, self._get_scope_for_perm(user_obj, perm), obj
        )

    def has_module_perms(self, user_obj, app_label: str) -> bool:
        if not user_obj.is_active or user_obj.is_anonymous:
            return False
        if user_obj.is_superuser:
            return True
        return any(
            perm.startswith(f"{app_label}.")
            for perm in self.get_all_permissions(user_obj)
        )

    def _get_scope_for_perm(self, user, perm: str) -> PermissionScope:
        """
        Resolves the broadest scope the user holds for a given permission string
        (e.g. "projects.change_project"). Traverses via PermissionCategory →
        group/user assignments rather than the module+codename path used by
        get_effective_scope(), because at object-check time only the auth
        permission string is available.
        """

        from apps.permissions.models import (
            GroupPermissionCategory,
            UserPermissionCategory,
        )

        app_label, codename = perm.split(".", 1)

        group_scopes = GroupPermissionCategory.objects.filter(
            group__user=user,
            category__permissions__content_type__app_label=app_label,
            category__permissions__codename=codename,
        ).values_list("scope", flat=True)

        user_scopes = UserPermissionCategory.objects.filter(
            user=user,
            category__permissions__content_type__app_label=app_label,
            category__permissions__codename=codename,
        ).values_list("scope", flat=True)

        all_scopes = [*group_scopes, *user_scopes]

        if not all_scopes:
            return PermissionScope.NONE  # type: ignore[return-value]

        return PermissionScope(max(all_scopes))  # type: ignore[return-value]

    def _scope_covers_object(self, user, scope: PermissionScope, obj) -> bool:
        """Checks whether the resolved scope grants access to a specific object."""
        match scope:
            case PermissionScope.ALL:
                return True
            case PermissionScope.TEAM:
                if hasattr(obj, "team"):
                    return obj.team.members.filter(pk=user.pk).exists()
                return False
            case PermissionScope.SELF:
                if hasattr(obj, "created_by_id"):
                    return obj.created_by_id == user.pk
                return False
            case _:
                return False
