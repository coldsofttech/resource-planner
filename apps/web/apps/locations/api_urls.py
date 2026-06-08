from django.urls import path

from apps.locations.api_views import LocationViewSet

urlpatterns = [
    path(
        "locations/",
        LocationViewSet.as_view({"get": "list", "post": "create"}),
        name="locations-list",
    ),
    path(
        "locations/stats/",
        LocationViewSet.as_view({"get": "statistics"}),
        name="locations-stats",
    ),
    # Options — must precede locations/<code>/ to avoid <code> matching "options"
    path(
        "locations/options/",
        LocationViewSet.as_view({"get": "options"}),
        name="locations-options",
    ),
    # Import — must precede locations/<code>/ to avoid <code> matching "import"
    path(
        "locations/import/specs/",
        LocationViewSet.as_view({"get": "import_specs"}),
        name="locations-import-specs",
    ),
    path(
        "locations/import/sample/",
        LocationViewSet.as_view({"get": "import_sample"}),
        name="locations-import-sample",
    ),
    path(
        "locations/import/",
        LocationViewSet.as_view({"post": "import_bulk"}),
        name="locations-import",
    ),
    # Export — specs must precede export/ to avoid prefix clash
    path(
        "locations/export/specs/",
        LocationViewSet.as_view({"get": "export_specs"}),
        name="locations-export-specs",
    ),
    path(
        "locations/export/",
        LocationViewSet.as_view({"get": "export"}),
        name="locations-export",
    ),
    path(
        "locations/<str:code>/",
        LocationViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="locations-detail",
    ),
    path(
        "locations/<str:code>/activate/",
        LocationViewSet.as_view({"post": "activate"}),
        name="locations-activate",
    ),
    path(
        "locations/<str:code>/deactivate/",
        LocationViewSet.as_view({"post": "deactivate"}),
        name="locations-deactivate",
    ),
    path(
        "locations/<str:code>/set-default/",
        LocationViewSet.as_view({"post": "set_default"}),
        name="locations-set-default",
    ),
]
