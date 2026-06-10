from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class LeavesListView(ProtectedView):
    template_name = "leaves/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_leave"] = "leaves.add_leave" in perms
        ctx["can_change_leave"] = "leaves.change_leave" in perms
        ctx["can_delete_leave"] = "leaves.delete_leave" in perms
        ctx["can_import_leave"] = "leaves.import_leave" in perms
        ctx["can_export_leave"] = "leaves.export_leave" in perms
        return ctx
