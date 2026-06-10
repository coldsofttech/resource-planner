from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class RolesListView(ProtectedView):
    template_name = "roles/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_role"] = "roles.add_role" in perms
        ctx["can_change_role"] = "roles.change_role" in perms
        ctx["can_delete_role"] = "roles.delete_role" in perms
        ctx["can_import_role"] = "roles.import_role" in perms
        ctx["can_export_role"] = "roles.export_role" in perms
        return ctx


class RoleDetailView(ProtectedView):
    template_name = "roles/detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        ctx["role_code"] = self.kwargs["code"]
        perms = get_user_permissions(self.request.user)
        ctx["can_change_role"] = "roles.change_role" in perms
        return ctx
