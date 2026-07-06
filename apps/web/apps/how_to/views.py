from django.http import Http404

from apps.core.views import BaseView

_GUIDE_MODULES = {
    "": "index",
    "financial-years": "financial-years",
    "sprints": "sprints",
    "sprint-forecast": "sprint-forecast",
    "sprint-actuals": "sprint-actuals",
    "projects": "projects",
    "estimates": "estimates",
    "project-sizes": "project-sizes",
    "project-links": "project-links",
    "project-attachments": "project-attachments",
    "project-budgets": "project-budgets",
    "project-actuals": "project-actuals",
    "project-contacts": "project-contacts",
    "project-comments": "project-comments",
    "programmes": "programmes",
    "teams": "teams",
    "members": "members",
    "leaves": "leaves",
    "business-units": "business-units",
    "roles": "roles",
    "skills": "skills",
    "employment-types": "employment-types",
    "locations": "locations",
    "holidays": "holidays",
    "tags": "tags",
    "recharge-types": "recharge-types",
}


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
    """Serves per-module guide pages. Slug '' renders the index/overview page."""

    def get_template_names(self) -> list[str]:
        slug = self.kwargs.get("slug", "")
        template_key = _GUIDE_MODULES.get(slug)
        if template_key is None:
            raise Http404
        return [f"how_to/guide/{template_key}.html"]

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug", "")
        ctx["guide_section"] = _GUIDE_MODULES.get(slug, "index")
        if self.request.user.is_authenticated:
            ctx["cta_url"] = "/dashboard/"
            ctx["cta_label"] = "Go to app"
            ctx["cta_footer_label"] = "Go to app"
        else:
            ctx["cta_url"] = "/login/"
            ctx["cta_label"] = "Sign in"
            ctx["cta_footer_label"] = "Sign in to get started"
        return ctx
