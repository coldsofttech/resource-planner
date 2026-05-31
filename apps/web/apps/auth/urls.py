from django.shortcuts import redirect
from django.urls import path

from apps.auth.views import ForgotPasswordView, LoginView, RegisterView


def _root_redirect(request):
    if request.user.is_authenticated:
        return redirect("/dashboard/")
    return redirect("/login/")


urlpatterns = [
    path("", _root_redirect, name="root"),
    path("login/", LoginView.as_view(), name="login"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("register/", RegisterView.as_view(), name="register"),
]
