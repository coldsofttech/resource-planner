from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class RechargeTypesListView(ProtectedView):
    template_name = "recharges/types/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_recharge_type"] = "recharges.add_rechargetype" in perms
        ctx["can_change_recharge_type"] = "recharges.change_rechargetype" in perms
        ctx["can_delete_recharge_type"] = "recharges.delete_rechargetype" in perms
        ctx["can_import_recharge_type"] = "recharges.import_rechargetype" in perms
        ctx["can_export_recharge_type"] = "recharges.export_rechargetype" in perms
        return ctx


class RechargeTypeDetailView(ProtectedView):
    template_name = "recharges/types/detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_mapping"] = "recharges.add_projecttypemapping" in perms
        ctx["can_change_mapping"] = "recharges.change_projecttypemapping" in perms
        ctx["can_delete_mapping"] = "recharges.delete_projecttypemapping" in perms
        ctx["can_import_mapping"] = "recharges.import_projecttypemapping" in perms
        ctx["can_export_mapping"] = "recharges.export_projecttypemapping" in perms
        return ctx
