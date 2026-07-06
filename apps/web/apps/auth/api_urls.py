from django.urls import path

from apps.auth.api_views import (
    AuthViewSet,
    ForgotPasswordViewSet,
    RegisterViewSet,
    SetPasswordViewSet,
)

urlpatterns = [
    path(
        "auth/login/",
        AuthViewSet.as_view({"post": "login"}),
        name="auth-login",
    ),
    path(
        "auth/register/",
        RegisterViewSet.as_view({"post": "register"}),
        name="auth-register",
    ),
    path(
        "auth/forgot-password/",
        ForgotPasswordViewSet.as_view({"post": "request_reset"}),
        name="auth-fp-request",
    ),
    path(
        "auth/forgot-password/verify/",
        ForgotPasswordViewSet.as_view({"post": "verify_code"}),
        name="auth-fp-verify",
    ),
    path(
        "auth/forgot-password/reset/",
        ForgotPasswordViewSet.as_view({"post": "reset_password"}),
        name="auth-fp-reset",
    ),
    path(
        "auth/logout/",
        AuthViewSet.as_view({"post": "logout"}),
        name="auth-logout",
    ),
    path(
        "auth/me/",
        AuthViewSet.as_view({"get": "me"}),
        name="auth-me",
    ),
    path(
        "auth/force-change-password/",
        AuthViewSet.as_view({"post": "force_change_password"}),
        name="auth-force-change-password",
    ),
    path(
        "auth/set-password/",
        SetPasswordViewSet.as_view({"post": "set_password"}),
        name="auth-set-password",
    ),
]
