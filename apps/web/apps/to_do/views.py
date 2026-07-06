from apps.core.views import ProtectedView


class ToDoListView(ProtectedView):
    template_name = "to_do/index.html"


class ToDoPreferencesView(ProtectedView):
    template_name = "to_do/preferences.html"
