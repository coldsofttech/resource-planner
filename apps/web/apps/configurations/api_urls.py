from django.urls import path

from apps.configurations.api_views import AIConfigViewSet, SecurityConfigViewSet

urlpatterns = [
    path(
        "ai/config/",
        AIConfigViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="ai-config",
    ),
    path(
        "security/config/",
        SecurityConfigViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="security-config",
    ),
]
