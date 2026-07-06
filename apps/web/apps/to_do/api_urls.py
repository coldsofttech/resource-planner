from django.urls import path

from apps.to_do.api_views import TodoPreferenceViewSet, TodoViewSet

urlpatterns = [
    path(
        "to-do/",
        TodoViewSet.as_view({"get": "list", "post": "create"}),
        name="to-do-list",
    ),
    path(
        "to-do/open-count/",
        TodoViewSet.as_view({"get": "open_count"}),
        name="to-do-open-count",
    ),
    path(
        "to-do/due-reminders/",
        TodoViewSet.as_view({"get": "due_reminders"}),
        name="to-do-due-reminders",
    ),
    path(
        "to-do/preferences/",
        TodoPreferenceViewSet.as_view({"get": "list"}),
        name="to-do-preferences-list",
    ),
    path(
        "to-do/preferences/<str:pk>/",
        TodoPreferenceViewSet.as_view({"patch": "partial_update"}),
        name="to-do-preferences-detail",
    ),
    path(
        "to-do/<str:code>/",
        TodoViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="to-do-detail",
    ),
    path(
        "to-do/<str:code>/complete/",
        TodoViewSet.as_view({"post": "complete"}),
        name="to-do-complete",
    ),
    path(
        "to-do/<str:code>/reopen/",
        TodoViewSet.as_view({"post": "reopen"}),
        name="to-do-reopen",
    ),
]
