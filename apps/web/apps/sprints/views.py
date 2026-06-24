from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class SprintsListView(ProtectedView):
    template_name = "sprints/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_sprint"] = "sprints.add_sprint" in perms
        ctx["can_change_sprint"] = "sprints.change_sprint" in perms
        ctx["can_delete_sprint"] = "sprints.delete_sprint" in perms
        ctx["can_import_sprint"] = "sprints.import_sprint" in perms
        ctx["can_export_sprint"] = "sprints.export_sprint" in perms
        ctx["can_generate_sprint"] = "sprints.generate_sprint" in perms
        ctx["can_close_sprint"] = "sprints.close_sprint" in perms
        return ctx


class SprintDetailView(ProtectedView):
    template_name = "sprints/detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["sprint_code"] = self.kwargs.get("sprint_code", "")
        ctx["can_change_sprint"] = "sprints.change_sprint" in perms
        return ctx


class SprintForecastView(ProtectedView):
    template_name = "sprints/forecast.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_import_forecast"] = "sprints.import_forecast" in perms
        return ctx


class SprintForecastImportDetailView(ProtectedView):
    template_name = "sprints/forecast_import_detail.html"


class SprintActualsView(ProtectedView):
    template_name = "sprints/actuals.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_import_actuals"] = "sprints.import_actuals" in perms
        return ctx


class SprintActualsImportDetailView(ProtectedView):
    template_name = "sprints/actuals_import_detail.html"
