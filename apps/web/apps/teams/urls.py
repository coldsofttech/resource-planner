from django.urls import path

from apps.teams.views import TeamsListView

urlpatterns = [
    path("teams/", TeamsListView.as_view(), name="teams-list"),
]
