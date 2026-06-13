from django.urls import path

from apps.projects.views import (
    ProgrammesListView,
    ProjectStatusesListView,
    ProjectTypesListView,
)

urlpatterns = [
    path("programmes/", ProgrammesListView.as_view(), name="programmes-list"),
    path("projects/types/", ProjectTypesListView.as_view(), name="project-types-list"),
    path(
        "projects/statuses/",
        ProjectStatusesListView.as_view(),
        name="project-statuses-list",
    ),
]
