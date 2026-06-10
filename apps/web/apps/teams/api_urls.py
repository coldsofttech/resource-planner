from django.urls import path

from apps.teams.api_views import TeamViewSet

urlpatterns = [
    path(
        "teams/",
        TeamViewSet.as_view({"get": "list", "post": "create"}),
        name="teams-list",
    ),
    path(
        "teams/stats/",
        TeamViewSet.as_view({"get": "statistics"}),
        name="teams-stats",
    ),
    # Options — must precede teams/<code>/ to avoid <code> matching "options"
    path(
        "teams/options/",
        TeamViewSet.as_view({"get": "options"}),
        name="teams-options",
    ),
    # Import — must precede teams/<code>/ to avoid <code> matching "import"
    path(
        "teams/import/specs/",
        TeamViewSet.as_view({"get": "import_specs"}),
        name="teams-import-specs",
    ),
    path(
        "teams/import/sample/",
        TeamViewSet.as_view({"get": "import_sample"}),
        name="teams-import-sample",
    ),
    path(
        "teams/import/",
        TeamViewSet.as_view({"post": "import_bulk"}),
        name="teams-import",
    ),
    # Export — same ordering reason; specs must precede export/ to avoid prefix clash
    path(
        "teams/export/specs/",
        TeamViewSet.as_view({"get": "export_specs"}),
        name="teams-export-specs",
    ),
    path(
        "teams/export/",
        TeamViewSet.as_view({"get": "export"}),
        name="teams-export",
    ),
    path(
        "teams/<str:code>/",
        TeamViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="teams-detail",
    ),
    path(
        "teams/<str:code>/activate/",
        TeamViewSet.as_view({"post": "activate"}),
        name="teams-activate",
    ),
    path(
        "teams/<str:code>/deactivate/",
        TeamViewSet.as_view({"post": "deactivate"}),
        name="teams-deactivate",
    ),
    path(
        "teams/<str:code>/members/",
        TeamViewSet.as_view({"get": "members"}),
        name="teams-members",
    ),
]
