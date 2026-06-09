from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class BaseView(TemplateView):
    """Lightweight base view for server-rendered pages."""

    extra_context: dict[str, object] = {}


class ProtectedView(LoginRequiredMixin, BaseView):
    """BaseView variant that requires authentication. Use for all logged-in pages."""
