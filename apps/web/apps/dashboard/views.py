from apps.core.views import ProtectedView


class DashboardView(ProtectedView):
    template_name = "dashboard/index.html"
