from django.views.generic import TemplateView


class BaseView(TemplateView):
    """Lightweight base view for server-rendered pages."""

    extra_context: dict[str, object] = {}
