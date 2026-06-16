from apps.core.views import BaseView


class HowToView(BaseView):
    template_name = "how_to/index.html"


class HowToSetupView(BaseView):
    template_name = "how_to/setup.html"


class HowToGuideView(BaseView):
    template_name = "how_to/guide.html"
