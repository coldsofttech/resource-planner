from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class MembersView(ProtectedView):
    template_name = "users/members.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_members"] = "auth.view_user" in perms
        ctx["can_change_workforce"] = "users.change_user_workforce" in perms
        ctx["can_export_members"] = "users.export_member" in perms
        ctx["can_assign_team"] = "teams.assign_team" in perms
        return ctx
