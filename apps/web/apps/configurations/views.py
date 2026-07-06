from apps.core.views import ProtectedView


class AIConfigView(ProtectedView):
    template_name = "configurations/ai-config.html"


class SecurityConfigView(ProtectedView):
    template_name = "configurations/security-config.html"
