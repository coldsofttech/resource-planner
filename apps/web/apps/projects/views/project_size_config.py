from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class ProjectSizesConfigView(ProtectedView):
    template_name = "projects/sizes/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_size_config"] = "configurations.change_configuration" in perms
        return ctx
