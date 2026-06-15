from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class TagsListView(ProtectedView):
    template_name = "tags/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_export_tag"] = "tags.export_tag" in perms
        return ctx
