from django.urls import path

from apps.sprints.api_views import (
    SprintDataImportActualViewSet,
    SprintDataImportForecastViewSet,
    SprintDataImportRowViewSet,
    SprintViewSet,
)

urlpatterns = [
    path(
        "sprints/",
        SprintViewSet.as_view({"get": "list", "post": "create"}),
        name="sprint-list",
    ),
    path(
        "sprints/stats/",
        SprintViewSet.as_view({"get": "statistics"}),
        name="sprint-stats",
    ),
    # Static action paths must precede sprints/<code>/ to avoid code matching them
    path(
        "sprints/active/",
        SprintViewSet.as_view({"get": "active"}),
        name="sprint-active",
    ),
    path(
        "sprints/options/",
        SprintViewSet.as_view({"get": "options"}),
        name="sprint-options",
    ),
    path(
        "sprints/generate/",
        SprintViewSet.as_view({"post": "generate"}),
        name="sprint-generate",
    ),
    path(
        "sprints/import/specs/",
        SprintViewSet.as_view({"get": "import_specs"}),
        name="sprint-import-specs",
    ),
    path(
        "sprints/import/sample/",
        SprintViewSet.as_view({"get": "import_sample"}),
        name="sprint-import-sample",
    ),
    path(
        "sprints/import/",
        SprintViewSet.as_view({"post": "import_bulk"}),
        name="sprint-import",
    ),
    path(
        "sprints/export/specs/",
        SprintViewSet.as_view({"get": "export_specs"}),
        name="sprint-export-specs",
    ),
    path(
        "sprints/export/",
        SprintViewSet.as_view({"get": "export"}),
        name="sprint-export",
    ),
    path(
        "sprints/<str:code>/capacity/rebuild/",
        SprintViewSet.as_view({"post": "capacity_rebuild"}),
        name="sprint-capacity-rebuild",
    ),
    path(
        "sprints/<str:code>/capacity/",
        SprintViewSet.as_view({"get": "capacity"}),
        name="sprint-capacity",
    ),
    path(
        "sprints/<str:code>/",
        SprintViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="sprint-detail",
    ),
    path(
        "sprints/<str:code>/activate/",
        SprintViewSet.as_view({"post": "activate"}),
        name="sprint-activate",
    ),
    path(
        "sprints/<str:code>/deactivate/",
        SprintViewSet.as_view({"post": "deactivate"}),
        name="sprint-deactivate",
    ),
    path(
        "sprints/<str:code>/set-active/",
        SprintViewSet.as_view({"post": "set_active"}),
        name="sprint-set-active",
    ),
    path(
        "sprints/<str:code>/close/",
        SprintViewSet.as_view({"post": "close"}),
        name="sprint-close",
    ),
    # Sprint data import — Forecast
    path(
        "sprints/<str:sprint_code>/forecast/review-complete/",
        SprintDataImportForecastViewSet.as_view({"post": "forecast_review_complete"}),
        name="sprint-forecast-review-complete",
    ),
    path(
        "sprints/<str:sprint_code>/forecast/template/",
        SprintDataImportForecastViewSet.as_view({"get": "download_template"}),
        name="sprint-forecast-template",
    ),
    path(
        "sprints/<str:sprint_code>/forecast/<str:team_code>/upload/",
        SprintDataImportForecastViewSet.as_view({"post": "upload"}),
        name="sprint-forecast-upload",
    ),
    path(
        "sprints/<str:sprint_code>/forecast/<str:team_code>/imports/",
        SprintDataImportForecastViewSet.as_view({"get": "list_imports"}),
        name="sprint-forecast-imports",
    ),
    # Sprint data import — Rows
    path(
        "sprints/<str:sprint_code>/forecast/<str:import_code>/",
        SprintDataImportRowViewSet.as_view({"get": "retrieve_import"}),
        name="sprint-forecast-import-detail",
    ),
    path(
        "sprints/<str:sprint_code>/forecast/<str:import_code>/rows/",
        SprintDataImportRowViewSet.as_view({"get": "list_rows", "post": "create_row"}),
        name="sprint-forecast-import-rows",
    ),
    path(
        "sprints/<str:sprint_code>/forecast/<str:import_code>/rows/<str:row_code>/",
        SprintDataImportRowViewSet.as_view(
            {"patch": "update_row", "delete": "delete_row"}
        ),
        name="sprint-forecast-import-row-detail",
    ),
    path(
        "sprints/<str:sprint_code>/forecast/<str:import_code>/review/",
        SprintDataImportRowViewSet.as_view({"post": "review_import"}),
        name="sprint-forecast-import-review",
    ),
    path(
        "sprints/<str:sprint_code>/forecast/<str:import_code>/confirm/",
        SprintDataImportRowViewSet.as_view({"post": "confirm_import"}),
        name="sprint-forecast-import-confirm",
    ),
    # Sprint data import — Actuals
    path(
        "sprints/<str:sprint_code>/actuals/template/",
        SprintDataImportActualViewSet.as_view({"get": "download_template"}),
        name="sprint-actuals-template",
    ),
    path(
        "sprints/<str:sprint_code>/actuals/<str:team_code>/upload/",
        SprintDataImportActualViewSet.as_view({"post": "upload"}),
        name="sprint-actuals-upload",
    ),
    path(
        "sprints/<str:sprint_code>/actuals/<str:team_code>/imports/",
        SprintDataImportActualViewSet.as_view({"get": "list_imports"}),
        name="sprint-actuals-imports",
    ),
]
