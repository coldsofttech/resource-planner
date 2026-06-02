from apps.core.views import BaseView


class DashboardView(BaseView):
    template_name = "dashboard/index.html"
