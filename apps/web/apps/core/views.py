from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.template import loader
from django.views.generic import TemplateView


class BaseView(TemplateView):
    """Lightweight base view for server-rendered pages."""

    extra_context: dict[str, object] = {}


class ProtectedView(LoginRequiredMixin, BaseView):
    """BaseView variant that requires authentication. Use for all logged-in pages."""


def _render_error(
    request: HttpRequest, template_name: str, status: int
) -> HttpResponse:
    # Render error templates without RequestContext so context processors never run.
    # This is critical for early-middleware errors (e.g. DisallowedHost) where
    # request.user has not yet been set by AuthenticationMiddleware.
    # The template receives `request` directly and can still check request.user.
    try:
        template = loader.get_template(template_name)
        return HttpResponse(template.render({"request": request}), status=status)
    except Exception:
        return HttpResponse(
            f"<h1>{status} Error</h1>", status=status, content_type="text/html"
        )


def bad_request(
    request: HttpRequest, exception: Exception | None = None
) -> HttpResponse:
    return _render_error(request, "400.html", 400)


def permission_denied(
    request: HttpRequest, exception: Exception | None = None
) -> HttpResponse:
    return _render_error(request, "403.html", 403)


def page_not_found(
    request: HttpRequest, exception: Exception | None = None
) -> HttpResponse:
    return _render_error(request, "404.html", 404)


def server_error(request: HttpRequest) -> HttpResponse:
    return _render_error(request, "500.html", 500)
