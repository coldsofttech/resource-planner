from apps.core.views import BaseView


class HowToView(BaseView):
    template_name = "how_to/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            ctx["cta_url"] = "/dashboard/"
            ctx["cta_label"] = "Go to app"
        else:
            ctx["cta_url"] = "/login/"
            ctx["cta_label"] = "Sign in"
        return ctx


class HowToSetupView(BaseView):
    template_name = "how_to/setup.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            ctx["cta_url"] = "/dashboard/"
            ctx["cta_label"] = "Go to app"
            ctx["cta_icon"] = ""
        else:
            ctx["cta_url"] = "/setup/"
            ctx["cta_label"] = "Open Setup"
            ctx["cta_icon"] = "bi-arrow-right"
        return ctx


class HowToGuideView(BaseView):
    template_name = "how_to/guide.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            ctx["cta_url"] = "/dashboard/"
            ctx["cta_label"] = "Go to app"
            ctx["cta_footer_label"] = "Go to app"
        else:
            ctx["cta_url"] = "/login/"
            ctx["cta_label"] = "Sign in"
            ctx["cta_footer_label"] = "Sign in to get started"
        return ctx
