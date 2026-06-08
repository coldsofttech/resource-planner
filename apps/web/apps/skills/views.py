from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class SkillsListView(ProtectedView):
    template_name = "skills/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_skill"] = "skills.add_skill" in perms
        ctx["can_change_skill"] = "skills.change_skill" in perms
        ctx["can_delete_skill"] = "skills.delete_skill" in perms
        ctx["can_import_skill"] = "skills.import_skill" in perms
        ctx["can_export_skill"] = "skills.export_skill" in perms
        return ctx
