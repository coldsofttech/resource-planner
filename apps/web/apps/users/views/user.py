from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class ProfileView(ProtectedView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_workforce"] = "users.change_user_workforce" in perms
        return ctx


class UsersAdminView(ProtectedView):
    template_name = "users/users.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth

        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)

        try:
            auth_mode = Auth.get_auth_mode()
            is_classic_auth = auth_mode == AuthMode.CLASSIC
        except Exception:
            is_classic_auth = False

        ctx["can_view_users"] = "auth.view_user" in perms
        ctx["can_add_user"] = "auth.add_user" in perms
        ctx["can_change_user"] = "auth.change_user" in perms
        ctx["can_delete_user"] = "auth.delete_user" in perms
        ctx["can_view_user_permissions"] = (
            "permissions.view_userpermissioncategory" in perms
        )
        ctx["can_manage_user_permissions"] = (
            "permissions.add_userpermissioncategory" in perms
        )
        ctx["is_classic_auth"] = is_classic_auth
        return ctx


class UserDetailView(ProtectedView):
    template_name = "users/user_detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth

        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)

        try:
            auth_mode = Auth.get_auth_mode()
            is_classic_auth = auth_mode == AuthMode.CLASSIC
        except Exception:
            is_classic_auth = False

        ctx["can_change_user"] = "auth.change_user" in perms
        ctx["can_view_user_permissions"] = (
            "permissions.view_userpermissioncategory" in perms
        )
        ctx["can_manage_user_permissions"] = (
            "permissions.add_userpermissioncategory" in perms
        )
        ctx["is_classic_auth"] = is_classic_auth
        return ctx
