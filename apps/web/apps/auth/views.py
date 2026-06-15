from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.core.views import BaseView


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


@method_decorator(ensure_csrf_cookie, name="dispatch")
class RegisterView(BaseView):
    template_name = "auth/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("/dashboard/")
        return super().dispatch(request, *args, **kwargs)
