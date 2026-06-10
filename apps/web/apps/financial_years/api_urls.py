from django.urls import path

from apps.financial_years.api_views import FinancialYearViewSet

urlpatterns = [
    path(
        "fy/",
        FinancialYearViewSet.as_view({"get": "list", "post": "create"}),
        name="fy-list",
    ),
    path(
        "fy/stats/",
        FinancialYearViewSet.as_view({"get": "statistics"}),
        name="fy-stats",
    ),
    # Static action paths must precede fy/<code>/ to avoid code matching them
    path(
        "fy/active/",
        FinancialYearViewSet.as_view({"get": "active"}),
        name="fy-active",
    ),
    path(
        "fy/options/",
        FinancialYearViewSet.as_view({"get": "options"}),
        name="fy-options",
    ),
    path(
        "fy/import/specs/",
        FinancialYearViewSet.as_view({"get": "import_specs"}),
        name="fy-import-specs",
    ),
    path(
        "fy/import/sample/",
        FinancialYearViewSet.as_view({"get": "import_sample"}),
        name="fy-import-sample",
    ),
    path(
        "fy/import/",
        FinancialYearViewSet.as_view({"post": "import_bulk"}),
        name="fy-import",
    ),
    path(
        "fy/export/specs/",
        FinancialYearViewSet.as_view({"get": "export_specs"}),
        name="fy-export-specs",
    ),
    path(
        "fy/export/",
        FinancialYearViewSet.as_view({"get": "export"}),
        name="fy-export",
    ),
    path(
        "fy/<str:code>/",
        FinancialYearViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="fy-detail",
    ),
    path(
        "fy/<str:code>/activate/",
        FinancialYearViewSet.as_view({"post": "activate"}),
        name="fy-activate",
    ),
    path(
        "fy/<str:code>/deactivate/",
        FinancialYearViewSet.as_view({"post": "deactivate"}),
        name="fy-deactivate",
    ),
    path(
        "fy/<str:code>/set-active/",
        FinancialYearViewSet.as_view({"post": "set_active"}),
        name="fy-set-active",
    ),
]
