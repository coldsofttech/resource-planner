import json

from django.http import HttpRequest

from apps.permissions.selectors import get_user_permissions


def user_permissions(request: HttpRequest) -> dict[str, object]:
    if not request.user.is_authenticated:
        return {"rp_permissions_json": "[]", "rp_permissions": frozenset()}
    perms = get_user_permissions(request.user)
    return {
        "rp_permissions_json": json.dumps(sorted(perms)),
        "rp_permissions": frozenset(perms),
    }
