from django.urls import path

from apps.reports.api_views import (
    CustomReportViewSet,
    DemandCapacityReportConfigViewSet,
    DemandVsCapacityReportViewSet,
    KPIEstimateAccuracyConfigViewSet,
    KPIEstimateAccuracyReportViewSet,
    MonthlyFinanceReportViewSet,
    MonthlyWinsReportViewSet,
    ReportViewSet,
    SprintForecastVsActualsReportViewSet,
    WeeklyWinsReportViewSet,
)

urlpatterns = [
    path(
        "reports/standard/",
        ReportViewSet.as_view({"get": "list", "post": "create"}),
        name="reports-standard-list",
    ),
    # Weekly Wins standard report — must precede reports/standard/<slug:slug>/
    # since these are more specific literal sub-paths.
    path(
        "reports/standard/weekly-wins/data/",
        WeeklyWinsReportViewSet.as_view({"get": "data"}),
        name="reports-weekly-wins-data",
    ),
    path(
        "reports/standard/weekly-wins/export/specs/",
        WeeklyWinsReportViewSet.as_view({"get": "export_specs"}),
        name="reports-weekly-wins-export-specs",
    ),
    path(
        "reports/standard/weekly-wins/export/",
        WeeklyWinsReportViewSet.as_view({"get": "export"}),
        name="reports-weekly-wins-export",
    ),
    # Monthly Wins standard report — must precede reports/standard/<slug:slug>/
    # since these are more specific literal sub-paths.
    path(
        "reports/standard/monthly-wins/data/",
        MonthlyWinsReportViewSet.as_view({"get": "data"}),
        name="reports-monthly-wins-data",
    ),
    path(
        "reports/standard/monthly-wins/export/specs/",
        MonthlyWinsReportViewSet.as_view({"get": "export_specs"}),
        name="reports-monthly-wins-export-specs",
    ),
    path(
        "reports/standard/monthly-wins/export/",
        MonthlyWinsReportViewSet.as_view({"get": "export"}),
        name="reports-monthly-wins-export",
    ),
    # Sprint Forecast vs. Actuals standard report — must precede
    # reports/standard/<slug:slug>/ since these are more specific literal sub-paths.
    path(
        "reports/standard/sprint-forecast-vs-actuals/data/",
        SprintForecastVsActualsReportViewSet.as_view({"get": "data"}),
        name="reports-sprint-forecast-vs-actuals-data",
    ),
    path(
        "reports/standard/sprint-forecast-vs-actuals/export/specs/",
        SprintForecastVsActualsReportViewSet.as_view({"get": "export_specs"}),
        name="reports-sprint-forecast-vs-actuals-export-specs",
    ),
    path(
        "reports/standard/sprint-forecast-vs-actuals/export/",
        SprintForecastVsActualsReportViewSet.as_view({"get": "export"}),
        name="reports-sprint-forecast-vs-actuals-export",
    ),
    # Demand vs. Capacity standard report — must precede
    # reports/standard/<slug:slug>/ since these are more specific literal sub-paths.
    path(
        "reports/standard/demand-vs-capacity/data/",
        DemandVsCapacityReportViewSet.as_view({"get": "data"}),
        name="reports-demand-vs-capacity-data",
    ),
    path(
        "reports/standard/demand-vs-capacity/export/specs/",
        DemandVsCapacityReportViewSet.as_view({"get": "export_specs"}),
        name="reports-demand-vs-capacity-export-specs",
    ),
    path(
        "reports/standard/demand-vs-capacity/export/",
        DemandVsCapacityReportViewSet.as_view({"get": "export"}),
        name="reports-demand-vs-capacity-export",
    ),
    path(
        "reports/standard/demand-vs-capacity/configs/",
        DemandCapacityReportConfigViewSet.as_view({"get": "list", "post": "create"}),
        name="reports-demand-vs-capacity-config-list",
    ),
    path(
        "reports/standard/demand-vs-capacity/configs/<str:code>/",
        DemandCapacityReportConfigViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="reports-demand-vs-capacity-config-detail",
    ),
    # KPI Report — Estimate % Accuracy standard report — must precede
    # reports/standard/<slug:slug>/ since these are more specific literal sub-paths.
    path(
        "reports/standard/kpi-estimate-accuracy/data/",
        KPIEstimateAccuracyReportViewSet.as_view({"get": "data"}),
        name="reports-kpi-estimate-accuracy-data",
    ),
    path(
        "reports/standard/kpi-estimate-accuracy/export/specs/",
        KPIEstimateAccuracyReportViewSet.as_view({"get": "export_specs"}),
        name="reports-kpi-estimate-accuracy-export-specs",
    ),
    path(
        "reports/standard/kpi-estimate-accuracy/export/",
        KPIEstimateAccuracyReportViewSet.as_view({"get": "export"}),
        name="reports-kpi-estimate-accuracy-export",
    ),
    path(
        "reports/standard/kpi-estimate-accuracy/configs/",
        KPIEstimateAccuracyConfigViewSet.as_view({"get": "list", "post": "create"}),
        name="reports-kpi-estimate-accuracy-config-list",
    ),
    path(
        "reports/standard/kpi-estimate-accuracy/configs/<str:code>/",
        KPIEstimateAccuracyConfigViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="reports-kpi-estimate-accuracy-config-detail",
    ),
    # Monthly Finance Report standard report — must precede
    # reports/standard/<slug:slug>/ since these are more specific literal sub-paths.
    path(
        "reports/standard/monthly-finance-report/data/",
        MonthlyFinanceReportViewSet.as_view({"get": "data"}),
        name="reports-monthly-finance-report-data",
    ),
    path(
        "reports/standard/monthly-finance-report/export/specs/",
        MonthlyFinanceReportViewSet.as_view({"get": "export_specs"}),
        name="reports-monthly-finance-report-export-specs",
    ),
    path(
        "reports/standard/monthly-finance-report/export/",
        MonthlyFinanceReportViewSet.as_view({"get": "export"}),
        name="reports-monthly-finance-report-export",
    ),
    path(
        "reports/standard/<slug:slug>/",
        ReportViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="reports-standard-detail",
    ),
    path(
        "reports/standard/<slug:slug>/activate/",
        ReportViewSet.as_view({"post": "activate"}),
        name="reports-standard-activate",
    ),
    path(
        "reports/standard/<slug:slug>/deactivate/",
        ReportViewSet.as_view({"post": "deactivate"}),
        name="reports-standard-deactivate",
    ),
    path(
        "reports/custom/",
        CustomReportViewSet.as_view({"get": "list", "post": "create"}),
        name="reports-custom-list",
    ),
    # Custom report builder endpoints — must precede reports/custom/<str:code>/
    # since these are more specific literal sub-paths.
    path(
        "reports/custom/data-sources/",
        CustomReportViewSet.as_view({"get": "data_sources"}),
        name="reports-custom-data-sources",
    ),
    path(
        "reports/custom/preview/",
        CustomReportViewSet.as_view({"post": "preview"}),
        name="reports-custom-preview",
    ),
    path(
        "reports/custom/export/specs/",
        CustomReportViewSet.as_view({"get": "export_specs"}),
        name="reports-custom-export-specs",
    ),
    path(
        "reports/custom/export/",
        CustomReportViewSet.as_view({"get": "export"}),
        name="reports-custom-export",
    ),
    path(
        "reports/custom/<str:code>/",
        CustomReportViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="reports-custom-detail",
    ),
    path(
        "reports/custom/<str:code>/execute/",
        CustomReportViewSet.as_view({"post": "execute"}),
        name="reports-custom-execute",
    ),
    path(
        "reports/custom/<str:code>/share/",
        CustomReportViewSet.as_view({"get": "share", "post": "share"}),
        name="reports-custom-share-list",
    ),
    path(
        "reports/custom/<str:code>/share/<str:member_code>/",
        CustomReportViewSet.as_view({"delete": "share_detail"}),
        name="reports-custom-share-detail",
    ),
]
