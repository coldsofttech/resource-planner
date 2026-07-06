from django.urls import path

from apps.wins.views import (
    MonthlyWinDetailView,
    MonthlyWinsListView,
    MonthlyWinSurveyView,
    WinDetailView,
    WinsConfigView,
    WinsListView,
)

urlpatterns = [
    path("wins/monthly/", MonthlyWinsListView.as_view(), name="monthly-wins-list"),
    path(
        "wins/monthly/survey/<uuid:token>/",
        MonthlyWinSurveyView.as_view(),
        name="monthly-wins-survey",
    ),
    path(
        "wins/monthly/<str:code>/",
        MonthlyWinDetailView.as_view(),
        name="monthly-wins-detail",
    ),
    path("wins/", WinsListView.as_view(), name="wins-list"),
    path("wins/config/", WinsConfigView.as_view(), name="wins-config"),
    path("wins/<str:code>/", WinDetailView.as_view(), name="wins-detail"),
]
