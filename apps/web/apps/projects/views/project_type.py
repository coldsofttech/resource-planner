from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class ProjectTypesListView(ProtectedView):
    template_name = "projects/types/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_project_type"] = "projects.add_projecttype" in perms
        ctx["can_change_project_type"] = "projects.change_projecttype" in perms
        ctx["can_delete_project_type"] = "projects.delete_projecttype" in perms
        ctx["can_import_project_type"] = "projects.import_projecttype" in perms
        ctx["can_export_project_type"] = "projects.export_projecttype" in perms
        return ctx
