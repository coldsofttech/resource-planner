from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


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
