from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class TeamsListView(ProtectedView):
    template_name = "teams/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_team"] = "teams.add_team" in perms
        ctx["can_change_team"] = "teams.change_team" in perms
        ctx["can_delete_team"] = "teams.delete_team" in perms
        ctx["can_import_team"] = "teams.import_team" in perms
        ctx["can_export_team"] = "teams.export_team" in perms
        return ctx
