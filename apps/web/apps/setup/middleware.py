from django.shortcuts import redirect

_BYPASS_PREFIXES = (
    "/setup/",
    "/api/v1/setup/",
    "/static/",
    "/favicon",
    "/media/",
)


class SetupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if not any(path.startswith(p) for p in _BYPASS_PREFIXES):
            from apps.configurations.selectors import Setup

            if not Setup.is_setup_complete():
                return redirect("/setup/")

        return self.get_response(request)
