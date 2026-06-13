from django.urls import path

from apps.projects.api_views import (
    ProgrammeViewSet,
    ProjectStatusViewSet,
    ProjectSubStatusFlatOptionsViewSet,
    ProjectSubStatusGlobalViewSet,
    ProjectSubStatusViewSet,
    ProjectTypeViewSet,
)

urlpatterns = [
    path(
        "programmes/",
        ProgrammeViewSet.as_view({"get": "list", "post": "create"}),
        name="programmes-list",
    ),
    path(
        "programmes/stats/",
        ProgrammeViewSet.as_view({"get": "statistics"}),
        name="programmes-stats",
    ),
    path(
        "programmes/options/",
        ProgrammeViewSet.as_view({"get": "options"}),
        name="programmes-options",
    ),
    path(
        "programmes/import/specs/",
        ProgrammeViewSet.as_view({"get": "import_specs"}),
        name="programmes-import-specs",
    ),
    path(
        "programmes/import/sample/",
        ProgrammeViewSet.as_view({"get": "import_sample"}),
        name="programmes-import-sample",
    ),
    path(
        "programmes/import/",
        ProgrammeViewSet.as_view({"post": "import_bulk"}),
        name="programmes-import",
    ),
    path(
        "programmes/export/specs/",
        ProgrammeViewSet.as_view({"get": "export_specs"}),
        name="programmes-export-specs",
    ),
    path(
        "programmes/export/",
        ProgrammeViewSet.as_view({"get": "export"}),
        name="programmes-export",
    ),
    path(
        "programmes/<str:code>/",
        ProgrammeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="programmes-detail",
    ),
    path(
        "programmes/<str:code>/activate/",
        ProgrammeViewSet.as_view({"post": "activate"}),
        name="programmes-activate",
    ),
    path(
        "programmes/<str:code>/deactivate/",
        ProgrammeViewSet.as_view({"post": "deactivate"}),
        name="programmes-deactivate",
    ),
    path(
        "projects/types/",
        ProjectTypeViewSet.as_view({"get": "list", "post": "create"}),
        name="project-types-list",
    ),
    path(
        "projects/types/stats/",
        ProjectTypeViewSet.as_view({"get": "statistics"}),
        name="project-types-stats",
    ),
    path(
        "projects/types/options/",
        ProjectTypeViewSet.as_view({"get": "options"}),
        name="project-types-options",
    ),
    path(
        "projects/types/import/specs/",
        ProjectTypeViewSet.as_view({"get": "import_specs"}),
        name="project-types-import-specs",
    ),
    path(
        "projects/types/import/sample/",
        ProjectTypeViewSet.as_view({"get": "import_sample"}),
        name="project-types-import-sample",
    ),
    path(
        "projects/types/import/",
        ProjectTypeViewSet.as_view({"post": "import_bulk"}),
        name="project-types-import",
    ),
    path(
        "projects/types/export/specs/",
        ProjectTypeViewSet.as_view({"get": "export_specs"}),
        name="project-types-export-specs",
    ),
    path(
        "projects/types/export/",
        ProjectTypeViewSet.as_view({"get": "export"}),
        name="project-types-export",
    ),
    path(
        "projects/types/<str:code>/",
        ProjectTypeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-types-detail",
    ),
    path(
        "projects/types/<str:code>/activate/",
        ProjectTypeViewSet.as_view({"post": "activate"}),
        name="project-types-activate",
    ),
    path(
        "projects/types/<str:code>/deactivate/",
        ProjectTypeViewSet.as_view({"post": "deactivate"}),
        name="project-types-deactivate",
    ),
    path(
        "projects/statuses/",
        ProjectStatusViewSet.as_view({"get": "list"}),
        name="project-statuses-list",
    ),
    path(
        "projects/statuses/stats/",
        ProjectStatusViewSet.as_view({"get": "statistics"}),
        name="project-statuses-stats",
    ),
    path(
        "projects/statuses/options/",
        ProjectStatusViewSet.as_view({"get": "options"}),
        name="project-statuses-options",
    ),
    path(
        "projects/statuses/export/specs/",
        ProjectStatusViewSet.as_view({"get": "export_specs"}),
        name="project-statuses-export-specs",
    ),
    path(
        "projects/statuses/export/",
        ProjectStatusViewSet.as_view({"get": "export"}),
        name="project-statuses-export",
    ),
    path(
        "projects/statuses/<str:code>/",
        ProjectStatusViewSet.as_view({"get": "retrieve"}),
        name="project-statuses-detail",
    ),
    # Sub-status nested routes
    path(
        "projects/statuses/<str:status_code>/substatus/",
        ProjectSubStatusViewSet.as_view({"get": "list", "post": "create"}),
        name="project-sub-statuses-list",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/stats/",
        ProjectSubStatusViewSet.as_view({"get": "statistics"}),
        name="project-sub-statuses-stats",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/options/",
        ProjectSubStatusViewSet.as_view({"get": "options"}),
        name="project-sub-statuses-options",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/reorder/",
        ProjectSubStatusViewSet.as_view({"post": "reorder"}),
        name="project-sub-statuses-reorder",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/import/specs/",
        ProjectSubStatusViewSet.as_view({"get": "import_specs"}),
        name="project-sub-statuses-import-specs",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/import/sample/",
        ProjectSubStatusViewSet.as_view({"get": "import_sample"}),
        name="project-sub-statuses-import-sample",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/import/",
        ProjectSubStatusViewSet.as_view({"post": "import_bulk"}),
        name="project-sub-statuses-import",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/export/specs/",
        ProjectSubStatusViewSet.as_view({"get": "export_specs"}),
        name="project-sub-statuses-export-specs",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/export/",
        ProjectSubStatusViewSet.as_view({"get": "export"}),
        name="project-sub-statuses-export",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/<str:code>/",
        ProjectSubStatusViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-sub-statuses-detail",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/<str:code>/activate/",
        ProjectSubStatusViewSet.as_view({"post": "activate"}),
        name="project-sub-statuses-activate",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/<str:code>/deactivate/",
        ProjectSubStatusViewSet.as_view({"post": "deactivate"}),
        name="project-sub-statuses-deactivate",
    ),
    # Flat options endpoint (for project-substatus-field without status context)
    path(
        "projects/sub-statuses/options/",
        ProjectSubStatusFlatOptionsViewSet.as_view({"get": "options"}),
        name="project-sub-statuses-flat-options",
    ),
    # Global sub-status import/export (main_status_code as CSV column)
    path(
        "projects/sub-statuses/import/specs/",
        ProjectSubStatusGlobalViewSet.as_view({"get": "import_specs"}),
        name="project-sub-statuses-global-import-specs",
    ),
    path(
        "projects/sub-statuses/import/sample/",
        ProjectSubStatusGlobalViewSet.as_view({"get": "import_sample"}),
        name="project-sub-statuses-global-import-sample",
    ),
    path(
        "projects/sub-statuses/import/",
        ProjectSubStatusGlobalViewSet.as_view({"post": "import_bulk"}),
        name="project-sub-statuses-global-import",
    ),
    path(
        "projects/sub-statuses/export/specs/",
        ProjectSubStatusGlobalViewSet.as_view({"get": "export_specs"}),
        name="project-sub-statuses-global-export-specs",
    ),
    path(
        "projects/sub-statuses/export/",
        ProjectSubStatusGlobalViewSet.as_view({"get": "export"}),
        name="project-sub-statuses-global-export",
    ),
]
