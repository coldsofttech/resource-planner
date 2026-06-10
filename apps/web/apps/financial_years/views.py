from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class FinancialYearsListView(ProtectedView):
    template_name = "financial_years/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_fy"] = "financial_years.add_financialyear" in perms
        ctx["can_change_fy"] = "financial_years.change_financialyear" in perms
        ctx["can_delete_fy"] = "financial_years.delete_financialyear" in perms
        ctx["can_import_fy"] = "financial_years.import_financialyear" in perms
        ctx["can_export_fy"] = "financial_years.export_financialyear" in perms
        return ctx
