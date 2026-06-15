from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class BusinessUnitListView(ProtectedView):
    template_name = "business_units/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_businessunit"] = "business_units.add_businessunit" in perms
        ctx["can_change_businessunit"] = "business_units.change_businessunit" in perms
        ctx["can_delete_businessunit"] = "business_units.delete_businessunit" in perms
        ctx["can_import_businessunit"] = "business_units.import_businessunit" in perms
        ctx["can_export_businessunit"] = "business_units.export_businessunit" in perms
        return ctx
