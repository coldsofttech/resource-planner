from django.urls import path

from apps.teams.views import TeamDetailView, TeamsListView

urlpatterns = [
    path("teams/", TeamsListView.as_view(), name="teams-list"),
    path("teams/<str:code>/", TeamDetailView.as_view(), name="teams-detail"),
]
