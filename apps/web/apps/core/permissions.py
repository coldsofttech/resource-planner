from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    """
    Grants access when the authenticated user holds a specific permission,
    resolved via the active authentication backends (including
    PermissionCategoryBackend).

    Usage in get_permissions():
        return [HasPermission("permissions.add_grouppermissioncategory")]
    """

    def __init__(self, perm: str):
        self.perm = perm

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.has_perm(self.perm)
        )
