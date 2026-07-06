from django.shortcuts import redirect

_PASSWORD_POLICY_BYPASS_PREFIXES = (
    "/login/",
    "/change-password-required/",
    "/api/v1/auth/",
    "/api/v1/meta/",
    "/static/",
    "/favicon",
    "/media/",
)


class PasswordPolicyMiddleware:
    """Forces signed-in users with profile.must_change_password=True to the
    change-password page before they can reach anything else — e.g. when
    PASSWORD_ROTATION_DAYS has elapsed since their last password change."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if not any(path.startswith(p) for p in _PASSWORD_POLICY_BYPASS_PREFIXES):
            user = getattr(request, "user", None)
            if user is not None and user.is_authenticated:
                profile = getattr(user, "profile", None)
                if profile is not None and profile.must_change_password:
                    return redirect("/change-password-required/")

        return self.get_response(request)


class SessionTimeoutMiddleware:
    """Applies the configured SESSION_TIMEOUT_MINUTES to authenticated Django
    sessions. Renewed on every request, so it behaves as an idle timeout."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and hasattr(request, "session"):
            from apps.configurations.selectors import Auth

            try:
                timeout_minutes = Auth.get_session_timeout_minutes()
            except Exception:
                timeout_minutes = 0

            if timeout_minutes > 0:
                request.session.set_expiry(timeout_minutes * 60)

        return response
