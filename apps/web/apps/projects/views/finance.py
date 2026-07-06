from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class ProjectFinanceView(ProtectedView):
    template_name = "projects/finance/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_project"] = "projects.change_project" in perms
        return ctx
