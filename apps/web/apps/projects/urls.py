from django.urls import path

from apps.projects.views import (
    ProgrammesListView,
    ProjectDetailView,
    ProjectSizesConfigView,
    ProjectsListView,
    ProjectStatusesListView,
    ProjectTypesListView,
)

urlpatterns = [
    path("projects/", ProjectsListView.as_view(), name="projects-list"),
    path(
        "projects/sizes/", ProjectSizesConfigView.as_view(), name="project-sizes-config"
    ),
    path("projects/types/", ProjectTypesListView.as_view(), name="project-types-list"),
    path(
        "projects/statuses/",
        ProjectStatusesListView.as_view(),
        name="project-statuses-list",
    ),
    path("projects/<str:code>/", ProjectDetailView.as_view(), name="project-detail"),
    path("programmes/", ProgrammesListView.as_view(), name="programmes-list"),
]
