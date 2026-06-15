from django.urls import path

from apps.users.api_views import (
    GroupsAdminViewSet,
    MembersViewSet,
    UserMeViewSet,
    UsersAdminViewSet,
)

urlpatterns = [
    # ── Me (authenticated user self-service) — specific paths must come first ─
    path(
        "users/me/",
        UserMeViewSet.as_view({"get": "me"}),
        name="users-me",
    ),
    path(
        "users/me/preferences/",
        UserMeViewSet.as_view({"patch": "update_preferences"}),
        name="users-me-preferences",
    ),
    path(
        "users/me/profile/",
        UserMeViewSet.as_view({"patch": "update_profile"}),
        name="users-me-profile",
    ),
    path(
        "users/me/password/",
        UserMeViewSet.as_view({"post": "change_password"}),
        name="users-me-password",
    ),
    path(
        "users/me/avatar/",
        UserMeViewSet.as_view({"get": "get_avatar"}),
        name="users-me-avatar",
    ),
    path(
        "users/me/avatar/upload/",
        UserMeViewSet.as_view({"post": "upload_avatar"}),
        name="users-me-avatar-upload",
    ),
    # ── Options (timezones) ───────────────────────────────────────────────────
    path(
        "users/options/",
        UserMeViewSet.as_view({"get": "options"}),
        name="users-options",
    ),
    # ── Admin users — static paths before parameterised ──────────────────────
    path(
        "users/",
        UsersAdminViewSet.as_view({"get": "list", "post": "create"}),
        name="admin-users-list",
    ),
    path(
        "users/stats/",
        UsersAdminViewSet.as_view({"get": "stats"}),
        name="admin-users-stats",
    ),
    path(
        "users/export/specs/",
        UsersAdminViewSet.as_view({"get": "export_specs"}),
        name="admin-users-export-specs",
    ),
    path(
        "users/export/",
        UsersAdminViewSet.as_view({"get": "export"}),
        name="admin-users-export",
    ),
    # Per-user avatar (looked up by profile code) — before <code>/ catch-all
    path(
        "users/<str:code>/avatar/",
        UserMeViewSet.as_view({"get": "get_user_avatar"}),
        name="users-user-avatar",
    ),
    path(
        "users/<str:code>/activate/",
        UsersAdminViewSet.as_view({"post": "activate"}),
        name="admin-users-activate",
    ),
    path(
        "users/<str:code>/deactivate/",
        UsersAdminViewSet.as_view({"post": "deactivate"}),
        name="admin-users-deactivate",
    ),
    path(
        "users/<str:code>/reset-password/",
        UsersAdminViewSet.as_view({"post": "reset_password"}),
        name="admin-users-reset-password",
    ),
    path(
        "users/<str:code>/",
        UsersAdminViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="admin-users-detail",
    ),
    # ── Members (workforce admin) ─────────────────────────────────────────────
    path(
        "members/",
        MembersViewSet.as_view({"get": "list"}),
        name="members-list",
    ),
    path(
        "members/options/",
        MembersViewSet.as_view({"get": "options"}),
        name="members-options",
    ),
    path(
        "members/export/specs/",
        MembersViewSet.as_view({"get": "export_specs"}),
        name="members-export-specs",
    ),
    path(
        "members/export/",
        MembersViewSet.as_view({"get": "export"}),
        name="members-export",
    ),
    path(
        "members/<str:code>/assign-team/",
        MembersViewSet.as_view({"post": "assign_team"}),
        name="members-assign-team",
    ),
    path(
        "members/<str:code>/",
        MembersViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="members-detail",
    ),
    # ── Groups (admin) ────────────────────────────────────────────────────────
    path(
        "groups/",
        GroupsAdminViewSet.as_view({"get": "list", "post": "create"}),
        name="admin-groups-list",
    ),
    path(
        "groups/stats/",
        GroupsAdminViewSet.as_view({"get": "stats"}),
        name="admin-groups-stats",
    ),
    path(
        "groups/import/specs/",
        GroupsAdminViewSet.as_view({"get": "import_specs"}),
        name="admin-groups-import-specs",
    ),
    path(
        "groups/import/sample/",
        GroupsAdminViewSet.as_view({"get": "import_sample"}),
        name="admin-groups-import-sample",
    ),
    path(
        "groups/import/",
        GroupsAdminViewSet.as_view({"post": "import_bulk"}),
        name="admin-groups-import",
    ),
    path(
        "groups/export/specs/",
        GroupsAdminViewSet.as_view({"get": "export_specs"}),
        name="admin-groups-export-specs",
    ),
    path(
        "groups/export/",
        GroupsAdminViewSet.as_view({"get": "export"}),
        name="admin-groups-export",
    ),
    path(
        "groups/<str:code>/activate/",
        GroupsAdminViewSet.as_view({"post": "activate"}),
        name="admin-groups-activate",
    ),
    path(
        "groups/<str:code>/deactivate/",
        GroupsAdminViewSet.as_view({"post": "deactivate"}),
        name="admin-groups-deactivate",
    ),
    path(
        "groups/<str:code>/members/",
        GroupsAdminViewSet.as_view({"get": "members", "post": "members"}),
        name="admin-groups-members",
    ),
    path(
        "groups/<str:code>/members/<str:member_code>/",
        GroupsAdminViewSet.as_view({"delete": "unassign_member"}),
        name="admin-groups-members-unassign",
    ),
    path(
        "groups/<str:code>/",
        GroupsAdminViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="admin-groups-detail",
    ),
]
