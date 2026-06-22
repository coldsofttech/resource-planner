from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class ProjectsListView(ProtectedView):
    template_name = "projects/projects/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_project"] = "projects.add_project" in perms
        ctx["can_change_project"] = "projects.change_project" in perms
        ctx["can_delete_project"] = "projects.delete_project" in perms
        return ctx


class ProjectDetailView(ProtectedView):
    template_name = "projects/projects/detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_project"] = "projects.change_project" in perms
        ctx["can_change_estimate"] = "projects.change_projectestimate" in perms
        ctx["can_change_budget"] = "projects.change_projectbudget" in perms
        ctx["can_delete_budget"] = "projects.delete_projectbudget" in perms
        ctx["can_change_link"] = "projects.change_projectlink" in perms
        ctx["can_add_attachment"] = "projects.add_projectattachment" in perms
        ctx["can_delete_attachment"] = "projects.delete_projectattachment" in perms
        ctx["can_add_contact"] = "projects.add_projectcontact" in perms
        ctx["can_delete_contact"] = "projects.delete_projectcontact" in perms
        return ctx
