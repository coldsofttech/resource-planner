from django.urls import path

from apps.users.api_views import MembersViewSet, UserMeViewSet

urlpatterns = [
    # Full profile read
    path(
        "users/me/",
        UserMeViewSet.as_view({"get": "me"}),
        name="users-me",
    ),
    # Theme preference (used by top-bar theme toggle)
    path(
        "users/me/preferences/",
        UserMeViewSet.as_view({"patch": "update_preferences"}),
        name="users-me-preferences",
    ),
    # Profile fields update
    path(
        "users/me/profile/",
        UserMeViewSet.as_view({"patch": "update_profile"}),
        name="users-me-profile",
    ),
    # Password change
    path(
        "users/me/password/",
        UserMeViewSet.as_view({"post": "change_password"}),
        name="users-me-password",
    ),
    # Avatar serve / upload
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
    # Per-user avatar (for members table — looked up by profile code)
    path(
        "users/<str:code>/avatar/",
        UserMeViewSet.as_view({"get": "get_user_avatar"}),
        name="users-user-avatar",
    ),
    # Options (timezones)
    path(
        "users/options/",
        UserMeViewSet.as_view({"get": "options"}),
        name="users-options",
    ),
    # Members list, options, update, and export
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
]
