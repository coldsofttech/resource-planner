from django.urls import path

from apps.business_units.api_views import BusinessUnitViewSet

urlpatterns = [
    path(
        "bu/",
        BusinessUnitViewSet.as_view({"get": "list", "post": "create"}),
        name="bu-list",
    ),
    path(
        "bu/stats/",
        BusinessUnitViewSet.as_view({"get": "statistics"}),
        name="bu-stats",
    ),
    path(
        "bu/options/",
        BusinessUnitViewSet.as_view({"get": "options"}),
        name="bu-options",
    ),
    path(
        "bu/import/specs/",
        BusinessUnitViewSet.as_view({"get": "import_specs"}),
        name="bu-import-specs",
    ),
    path(
        "bu/import/sample/",
        BusinessUnitViewSet.as_view({"get": "import_sample"}),
        name="bu-import-sample",
    ),
    path(
        "bu/import/",
        BusinessUnitViewSet.as_view({"post": "import_bulk"}),
        name="bu-import",
    ),
    path(
        "bu/export/specs/",
        BusinessUnitViewSet.as_view({"get": "export_specs"}),
        name="bu-export-specs",
    ),
    path(
        "bu/export/",
        BusinessUnitViewSet.as_view({"get": "export"}),
        name="bu-export",
    ),
    path(
        "bu/<str:code>/",
        BusinessUnitViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="bu-detail",
    ),
    path(
        "bu/<str:code>/activate/",
        BusinessUnitViewSet.as_view({"post": "activate"}),
        name="bu-activate",
    ),
    path(
        "bu/<str:code>/deactivate/",
        BusinessUnitViewSet.as_view({"post": "deactivate"}),
        name="bu-deactivate",
    ),
]
