from django.urls import path

from apps.leaves.api_views import LeaveViewSet

urlpatterns = [
    path(
        "leaves/",
        LeaveViewSet.as_view({"get": "list", "post": "create"}),
        name="leaves-list",
    ),
    path(
        "leaves/stats/",
        LeaveViewSet.as_view({"get": "statistics"}),
        name="leaves-stats",
    ),
    # Import — must precede leaves/<code>/ to avoid <code> matching "import"
    path(
        "leaves/import/specs/",
        LeaveViewSet.as_view({"get": "import_specs"}),
        name="leaves-import-specs",
    ),
    path(
        "leaves/import/sample/",
        LeaveViewSet.as_view({"get": "import_sample"}),
        name="leaves-import-sample",
    ),
    path(
        "leaves/import/",
        LeaveViewSet.as_view({"post": "import_bulk"}),
        name="leaves-import",
    ),
    # Export — specs must precede export/ to avoid prefix clash
    path(
        "leaves/export/specs/",
        LeaveViewSet.as_view({"get": "export_specs"}),
        name="leaves-export-specs",
    ),
    path(
        "leaves/export/",
        LeaveViewSet.as_view({"get": "export"}),
        name="leaves-export",
    ),
    path(
        "leaves/<str:code>/",
        LeaveViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="leaves-detail",
    ),
]
