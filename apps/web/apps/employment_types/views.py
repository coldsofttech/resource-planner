from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class EmploymentTypesListView(ProtectedView):
    template_name = "employment_types/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_employment_type"] = "employment_types.add_employmenttype" in perms
        ctx["can_change_employment_type"] = (
            "employment_types.change_employmenttype" in perms
        )
        ctx["can_delete_employment_type"] = (
            "employment_types.delete_employmenttype" in perms
        )
        ctx["can_import_employment_type"] = (
            "employment_types.import_employmenttype" in perms
        )
        ctx["can_export_employment_type"] = (
            "employment_types.export_employmenttype" in perms
        )
        return ctx
