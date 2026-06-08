from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class LocationsListView(ProtectedView):
    template_name = "locations/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_location"] = "locations.add_location" in perms
        ctx["can_change_location"] = "locations.change_location" in perms
        ctx["can_delete_location"] = "locations.delete_location" in perms
        ctx["can_import_location"] = "locations.import_location" in perms
        ctx["can_export_location"] = "locations.export_location" in perms
        return ctx
