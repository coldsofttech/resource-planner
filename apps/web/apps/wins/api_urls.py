from django.urls import path

from apps.wins.api_views import (
    MonthlyWinsRecipientViewSet,
    MonthlyWinViewSet,
    SurveyViewSet,
    WinEntryViewSet,
    WinsConfigViewSet,
    WinViewSet,
)

urlpatterns = [
    # ── Monthly Wins (must precede the generic wins/<code>/ routes) ────────
    path(
        "wins/monthly/recipients/",
        MonthlyWinsRecipientViewSet.as_view({"get": "list", "post": "create"}),
        name="monthly-wins-recipients-list",
    ),
    path(
        "wins/monthly/recipients/<str:code>/",
        MonthlyWinsRecipientViewSet.as_view(
            {"patch": "partial_update", "delete": "destroy"}
        ),
        name="monthly-wins-recipients-detail",
    ),
    path(
        "wins/monthly/surveys/<str:survey_code>/admin-data/",
        MonthlyWinViewSet.as_view({"get": "survey_admin_data"}),
        name="monthly-wins-survey-admin-data",
    ),
    path(
        "wins/monthly/surveys/<str:survey_code>/override/",
        MonthlyWinViewSet.as_view({"post": "override_survey"}),
        name="monthly-wins-survey-override",
    ),
    path(
        "wins/monthly/survey/<uuid:token>/",
        SurveyViewSet.as_view({"get": "retrieve"}),
        name="monthly-wins-survey-public",
    ),
    path(
        "wins/monthly/survey/<uuid:token>/submit/",
        SurveyViewSet.as_view({"post": "submit"}),
        name="monthly-wins-survey-submit",
    ),
    path(
        "wins/monthly/",
        MonthlyWinViewSet.as_view({"get": "list", "post": "create"}),
        name="monthly-wins-list",
    ),
    path(
        "wins/monthly/options/",
        MonthlyWinViewSet.as_view({"get": "options"}),
        name="monthly-wins-options",
    ),
    path(
        "wins/monthly/<str:code>/",
        MonthlyWinViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="monthly-wins-detail",
    ),
    path(
        "wins/monthly/<str:code>/preview-teams/",
        MonthlyWinViewSet.as_view({"get": "preview_teams"}),
        name="monthly-wins-preview-teams",
    ),
    path(
        "wins/monthly/<str:code>/preview-survey/",
        MonthlyWinViewSet.as_view({"get": "preview_survey"}),
        name="monthly-wins-preview-survey",
    ),
    path(
        "wins/monthly/<str:code>/surveys/",
        MonthlyWinViewSet.as_view({"get": "surveys"}),
        name="monthly-wins-surveys",
    ),
    path(
        "wins/monthly/<str:code>/results/",
        MonthlyWinViewSet.as_view({"get": "results"}),
        name="monthly-wins-results",
    ),
    path(
        "wins/monthly/<str:code>/launch-phase1/",
        MonthlyWinViewSet.as_view({"post": "launch_phase1"}),
        name="monthly-wins-launch-phase1",
    ),
    path(
        "wins/monthly/<str:code>/complete-phase1/",
        MonthlyWinViewSet.as_view({"post": "complete_phase1"}),
        name="monthly-wins-complete-phase1",
    ),
    path(
        "wins/monthly/<str:code>/launch-phase2/",
        MonthlyWinViewSet.as_view({"post": "launch_phase2"}),
        name="monthly-wins-launch-phase2",
    ),
    path(
        "wins/monthly/<str:code>/complete-phase2/",
        MonthlyWinViewSet.as_view({"post": "complete_phase2"}),
        name="monthly-wins-complete-phase2",
    ),
    path(
        "wins/monthly/<str:code>/declare/",
        MonthlyWinViewSet.as_view({"post": "declare_winners"}),
        name="monthly-wins-declare",
    ),
    path(
        "wins/monthly/<str:code>/results-pdf/",
        MonthlyWinViewSet.as_view({"get": "results_pdf"}),
        name="monthly-wins-results-pdf",
    ),
    path(
        "wins/monthly/<str:code>/send-results/",
        MonthlyWinViewSet.as_view({"post": "send_results"}),
        name="monthly-wins-send-results",
    ),
    # ── Weekly Wins ──────────────────────────────────────────────────────────
    path(
        "wins/",
        WinViewSet.as_view({"get": "list", "post": "create"}),
        name="wins-list",
    ),
    path(
        "wins/options/",
        WinViewSet.as_view({"get": "options"}),
        name="wins-options",
    ),
    path(
        "wins/config/",
        WinsConfigViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="wins-config",
    ),
    path(
        "wins/<str:code>/",
        WinViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="wins-detail",
    ),
    path(
        "wins/<str:code>/review-complete/",
        WinViewSet.as_view({"post": "review_complete"}),
        name="wins-review-complete",
    ),
    path(
        "wins/<str:code>/review-pdf/",
        WinViewSet.as_view({"get": "review_pdf"}),
        name="wins-review-pdf",
    ),
    path(
        "wins/<str:code>/send-review/",
        WinViewSet.as_view({"post": "send_review"}),
        name="wins-send-review",
    ),
    path(
        "wins/<str:win_code>/entries/",
        WinEntryViewSet.as_view({"get": "list", "post": "create"}),
        name="wins-entries-list",
    ),
    path(
        "wins/<str:win_code>/entries/suggest/",
        WinEntryViewSet.as_view({"post": "suggest"}),
        name="wins-entries-suggest",
    ),
    path(
        "wins/<str:win_code>/entries/<str:code>/",
        WinEntryViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="wins-entries-detail",
    ),
]
