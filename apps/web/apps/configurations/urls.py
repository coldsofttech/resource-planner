from django.urls import path

from apps.configurations.views import AIConfigView, SecurityConfigView

urlpatterns = [
    path("configurations/ai/", AIConfigView.as_view(), name="ai-config"),
    path(
        "configurations/security/",
        SecurityConfigView.as_view(),
        name="security-config",
    ),
]
