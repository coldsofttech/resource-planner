from django.urls import path

from apps.employment_types.api_views import EmploymentTypeViewSet

urlpatterns = [
    path(
        "emp-types/",
        EmploymentTypeViewSet.as_view({"get": "list", "post": "create"}),
        name="emp-types-list",
    ),
    path(
        "emp-types/stats/",
        EmploymentTypeViewSet.as_view({"get": "statistics"}),
        name="emp-types-stats",
    ),
    # Options — must precede emp-types/<code>/ to avoid <code> matching "options"
    path(
        "emp-types/options/",
        EmploymentTypeViewSet.as_view({"get": "options"}),
        name="emp-types-options",
    ),
    # Import — must precede emp-types/<code>/ to avoid <code> matching "import"
    path(
        "emp-types/import/specs/",
        EmploymentTypeViewSet.as_view({"get": "import_specs"}),
        name="emp-types-import-specs",
    ),
    path(
        "emp-types/import/sample/",
        EmploymentTypeViewSet.as_view({"get": "import_sample"}),
        name="emp-types-import-sample",
    ),
    path(
        "emp-types/import/",
        EmploymentTypeViewSet.as_view({"post": "import_bulk"}),
        name="emp-types-import",
    ),
    # Export — specs must precede export/ to avoid prefix clash
    path(
        "emp-types/export/specs/",
        EmploymentTypeViewSet.as_view({"get": "export_specs"}),
        name="emp-types-export-specs",
    ),
    path(
        "emp-types/export/",
        EmploymentTypeViewSet.as_view({"get": "export"}),
        name="emp-types-export",
    ),
    path(
        "emp-types/<str:code>/",
        EmploymentTypeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="emp-types-detail",
    ),
    path(
        "emp-types/<str:code>/activate/",
        EmploymentTypeViewSet.as_view({"post": "activate"}),
        name="emp-types-activate",
    ),
    path(
        "emp-types/<str:code>/deactivate/",
        EmploymentTypeViewSet.as_view({"post": "deactivate"}),
        name="emp-types-deactivate",
    ),
    path(
        "emp-types/<str:code>/set-default/",
        EmploymentTypeViewSet.as_view({"post": "set_default"}),
        name="emp-types-set-default",
    ),
]
