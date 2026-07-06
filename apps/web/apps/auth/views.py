from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.core.views import BaseView, ProtectedView


def _password_policy_context() -> dict:
    """Rendered onto password-field(s) as attributes so client-side strength
    validation matches the configured PASSWORD_* policy (only meaningful for
    classic auth, but harmless to render otherwise)."""
    from apps.configurations.selectors import PasswordPolicy

    return {
        "pwd_min_length": PasswordPolicy.get_min_length(),
        "pwd_require_uppercase": PasswordPolicy.require_uppercase(),
        "pwd_require_lowercase": PasswordPolicy.require_lowercase(),
        "pwd_require_digits": PasswordPolicy.require_digits(),
        "pwd_require_special": PasswordPolicy.require_special(),
    }


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SetPasswordView(BaseView):
    template_name = "auth/set_password.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("/dashboard/")
        token = request.GET.get("token", "")
        if not token:
            return redirect("/login/")
        from apps.auth.services import AdminPasswordResetService

        token_obj = AdminPasswordResetService().validate_token(token)
        if token_obj is None:
            return redirect("/login/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_password_policy_context())
        return context


@method_decorator(ensure_csrf_cookie, name="dispatch")
class LoginView(BaseView):
    template_name = "auth/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("/dashboard/")
        return super().dispatch(request, *args, **kwargs)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ForgotPasswordView(BaseView):
    template_name = "auth/forgot_password.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("/dashboard/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_password_policy_context())
        return context


@method_decorator(ensure_csrf_cookie, name="dispatch")
class RegisterView(BaseView):
    template_name = "auth/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("/dashboard/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_password_policy_context())
        return context


class ForceChangePasswordView(ProtectedView):
    """Standalone page shown when profile.must_change_password is set —
    e.g. overdue password rotation. Access is enforced by
    PasswordPolicyMiddleware, which redirects here until the password
    is changed."""

    template_name = "auth/force_change_password.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)
            if profile is not None and not profile.must_change_password:
                return redirect("/dashboard/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_password_policy_context())
        return context
