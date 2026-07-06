from django.urls import path

from apps.notifications.views import NotificationPreferencesView, NotificationsListView

urlpatterns = [
    path(
        "notifications/preferences/",
        NotificationPreferencesView.as_view(),
        name="notifications-preferences",
    ),
    path("notifications/", NotificationsListView.as_view(), name="notifications-list"),
]
