from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class StandardReportsListView(ProtectedView):
    template_name = "reports/standard.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_report"] = "reports.view_report" in perms
        return ctx


class CustomReportsListView(ProtectedView):
    template_name = "reports/custom.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_customreport"] = "reports.add_customreport" in perms
        ctx["can_change_customreport"] = "reports.change_customreport" in perms
        ctx["can_delete_customreport"] = "reports.delete_customreport" in perms
        return ctx


class CustomReportBuilderView(ProtectedView):
    template_name = "reports/custom_builder.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_customreport"] = "reports.change_customreport" in perms
        return ctx


class WeeklyWinsReportView(ProtectedView):
    template_name = "reports/weekly_wins.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_report"] = "reports.view_report" in perms
        return ctx


class MonthlyWinsReportView(ProtectedView):
    template_name = "reports/monthly_wins.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_report"] = "reports.view_report" in perms
        return ctx


class MonthlyFinanceReportView(ProtectedView):
    template_name = "reports/monthly_finance_report.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_report"] = "reports.view_report" in perms
        return ctx


class SprintForecastVsActualsReportView(ProtectedView):
    template_name = "reports/sprint_forecast_vs_actuals.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_report"] = "reports.view_report" in perms
        return ctx


class DemandVsCapacityReportView(ProtectedView):
    template_name = "reports/demand_vs_capacity.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_report"] = "reports.view_report" in perms
        ctx["can_manage_config"] = (
            "reports.add_demandcapacityreportconfig" in perms
            or "reports.change_demandcapacityreportconfig" in perms
        )
        return ctx


class DemandVsCapacityConfigView(ProtectedView):
    template_name = "reports/demand_vs_capacity_config.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_config"] = "reports.add_demandcapacityreportconfig" in perms
        ctx["can_change_config"] = "reports.change_demandcapacityreportconfig" in perms
        ctx["can_delete_config"] = "reports.delete_demandcapacityreportconfig" in perms
        return ctx


class KPIEstimateAccuracyReportView(ProtectedView):
    template_name = "reports/kpi_estimate_accuracy.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_report"] = "reports.view_report" in perms
        ctx["can_manage_config"] = (
            "reports.add_kpiestimateaccuracyconfig" in perms
            or "reports.change_kpiestimateaccuracyconfig" in perms
        )
        return ctx


class KPIEstimateAccuracyConfigView(ProtectedView):
    template_name = "reports/kpi_estimate_accuracy_config.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_config"] = "reports.add_kpiestimateaccuracyconfig" in perms
        ctx["can_change_config"] = "reports.change_kpiestimateaccuracyconfig" in perms
        ctx["can_delete_config"] = "reports.delete_kpiestimateaccuracyconfig" in perms
        return ctx
