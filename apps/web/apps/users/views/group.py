from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class GroupsAdminView(ProtectedView):
    template_name = "users/groups.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_group"] = "users.change_group" in perms
        ctx["can_delete_group"] = "users.delete_group" in perms
        return ctx


class GroupDetailView(ProtectedView):
    template_name = "users/group_detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_group"] = "users.change_group" in perms
        ctx["group_code"] = self.kwargs.get("code", "")
        return ctx
