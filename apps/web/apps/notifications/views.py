from apps.core.views import ProtectedView


class NotificationsListView(ProtectedView):
    template_name = "notifications/index.html"


class NotificationPreferencesView(ProtectedView):
    template_name = "notifications/preferences.html"
