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


class ProjectStatusesListView(ProtectedView):
    template_name = "projects/statuses/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_export_project_status"] = "projects.export_projectstatus" in perms
        ctx["can_add_project_substatus"] = "projects.add_projectsubstatus" in perms
        ctx["can_change_project_substatus"] = (
            "projects.change_projectsubstatus" in perms
        )
        ctx["can_delete_project_substatus"] = (
            "projects.delete_projectsubstatus" in perms
        )
        ctx["can_import_project_substatus"] = (
            "projects.import_projectsubstatus" in perms
        )
        ctx["can_export_project_substatus"] = (
            "projects.export_projectsubstatus" in perms
        )
        return ctx
