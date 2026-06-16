from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class ProgrammesListView(ProtectedView):
    template_name = "projects/programmes/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_programme"] = "projects.add_programme" in perms
        ctx["can_change_programme"] = "projects.change_programme" in perms
        ctx["can_delete_programme"] = "projects.delete_programme" in perms
        ctx["can_import_programme"] = "projects.import_programme" in perms
        ctx["can_export_programme"] = "projects.export_programme" in perms
        return ctx
