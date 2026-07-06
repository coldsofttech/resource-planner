from django.urls import path

from apps.notifications.api_views import (
    NotificationPreferenceViewSet,
    NotificationViewSet,
)

urlpatterns = [
    path(
        "notifications/",
        NotificationViewSet.as_view({"get": "list", "post": "create"}),
        name="notifications-list",
    ),
    path(
        "notifications/unread-count/",
        NotificationViewSet.as_view({"get": "unread_count"}),
        name="notifications-unread-count",
    ),
    path(
        "notifications/mark-all-read/",
        NotificationViewSet.as_view({"post": "mark_all_read"}),
        name="notifications-mark-all-read",
    ),
    path(
        "notifications/preferences/",
        NotificationPreferenceViewSet.as_view({"get": "list"}),
        name="notifications-preferences-list",
    ),
    path(
        "notifications/preferences/<str:pk>/",
        NotificationPreferenceViewSet.as_view({"patch": "partial_update"}),
        name="notifications-preferences-detail",
    ),
    path(
        "notifications/<str:code>/",
        NotificationViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="notifications-detail",
    ),
    path(
        "notifications/<str:code>/read/",
        NotificationViewSet.as_view({"post": "mark_read"}),
        name="notifications-mark-read",
    ),
    path(
        "notifications/<str:code>/unread/",
        NotificationViewSet.as_view({"post": "mark_unread"}),
        name="notifications-mark-unread",
    ),
    path(
        "notifications/<str:code>/dismiss/",
        NotificationViewSet.as_view({"post": "dismiss"}),
        name="notifications-dismiss",
    ),
]
