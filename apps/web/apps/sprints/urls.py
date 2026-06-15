from django.urls import path

from apps.sprints.views import SprintDetailView, SprintsListView

urlpatterns = [
    path("sprints/", SprintsListView.as_view(), name="sprints-list"),
    path(
        "sprints/<str:sprint_code>/", SprintDetailView.as_view(), name="sprints-detail"
    ),
]
