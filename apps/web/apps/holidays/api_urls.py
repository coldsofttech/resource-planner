from django.urls import path

from apps.holidays.api_views import HolidayViewSet

urlpatterns = [
    path(
        "holidays/",
        HolidayViewSet.as_view({"get": "list", "post": "create"}),
        name="holidays-list",
    ),
    path(
        "holidays/stats/",
        HolidayViewSet.as_view({"get": "statistics"}),
        name="holidays-stats",
    ),
    # Options — must precede holidays/<code>/ to avoid <code> matching "options"
    path(
        "holidays/options/",
        HolidayViewSet.as_view({"get": "options"}),
        name="holidays-options",
    ),
    # Import — must precede holidays/<code>/ to avoid <code> matching "import"
    path(
        "holidays/import/specs/",
        HolidayViewSet.as_view({"get": "import_specs"}),
        name="holidays-import-specs",
    ),
    path(
        "holidays/import/sample/",
        HolidayViewSet.as_view({"get": "import_sample"}),
        name="holidays-import-sample",
    ),
    path(
        "holidays/import/",
        HolidayViewSet.as_view({"post": "import_bulk"}),
        name="holidays-import",
    ),
    # Export — specs must precede export/ to avoid prefix clash
    path(
        "holidays/export/specs/",
        HolidayViewSet.as_view({"get": "export_specs"}),
        name="holidays-export-specs",
    ),
    path(
        "holidays/export/",
        HolidayViewSet.as_view({"get": "export"}),
        name="holidays-export",
    ),
    path(
        "holidays/<str:code>/",
        HolidayViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="holidays-detail",
    ),
]
