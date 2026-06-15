import json
from typing import Any

from django.contrib.messages import get_messages
from django.http import HttpRequest

from apps.permissions.selectors import get_user_permissions


def user_permissions(request: HttpRequest) -> dict[str, Any]:
    if not request.user.is_authenticated:
        return {
            "rp_permissions_json": "[]",
            "rp_permissions": frozenset(),
            "rp_permissions_list": [],
        }
    perms = get_user_permissions(request.user)
    perm_list = sorted(perms)
    return {
        "rp_permissions_json": json.dumps(perm_list),
        "rp_permissions": frozenset(perms),
        "rp_permissions_list": perm_list,
    }


def messages_for_js(request: HttpRequest) -> dict[str, Any]:
    return {
        "messages_for_js": [
            {"type": str(m.tags), "message": str(m)} for m in get_messages(request)
        ]
    }
