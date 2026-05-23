from django.shortcuts import redirect

_BYPASS_PREFIXES = (
    "/setup/",
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
            from apps.setup.selectors import get_setup_status

            if not get_setup_status():
                return redirect("/setup/")

        return self.get_response(request)
