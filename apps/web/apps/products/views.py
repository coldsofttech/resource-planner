from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class ProductListView(ProtectedView):
    template_name = "products/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_product"] = "products.add_product" in perms
        ctx["can_change_product"] = "products.change_product" in perms
        ctx["can_delete_product"] = "products.delete_product" in perms
        ctx["can_import_product"] = "products.import_product" in perms
        ctx["can_export_product"] = "products.export_product" in perms
        return ctx
