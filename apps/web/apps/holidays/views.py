from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class HolidaysListView(ProtectedView):
    template_name = "holidays/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_holiday"] = "holidays.add_holiday" in perms
        ctx["can_change_holiday"] = "holidays.change_holiday" in perms
        ctx["can_delete_holiday"] = "holidays.delete_holiday" in perms
        ctx["can_import_holiday"] = "holidays.import_holiday" in perms
        ctx["can_export_holiday"] = "holidays.export_holiday" in perms
        return ctx
