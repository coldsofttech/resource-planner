from django.urls import path

from apps.sprints.views import (
    SprintDetailView,
    SprintForecastImportDetailView,
    SprintForecastView,
    SprintsListView,
)

urlpatterns = [
    path("sprints/", SprintsListView.as_view(), name="sprints-list"),
    path(
        "sprints/<str:sprint_code>/", SprintDetailView.as_view(), name="sprints-detail"
    ),
    path(
        "sprints/<str:sprint_code>/forecast/",
        SprintForecastView.as_view(),
        name="sprints-forecast",
    ),
    path(
        "sprints/<str:sprint_code>/forecast/<str:import_code>/",
        SprintForecastImportDetailView.as_view(),
        name="sprints-forecast-import-detail",
    ),
]
