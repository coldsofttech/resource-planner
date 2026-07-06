from django.urls import path

from .views import HowToGuideView, HowToSetupView, HowToView

urlpatterns = [
    path("docs/", HowToView.as_view(), name="how_to"),
    path("docs/setup/", HowToSetupView.as_view(), name="how_to_setup"),
    path("docs/guide/", HowToGuideView.as_view(), name="how_to_guide"),
    path(
        "docs/guide/<slug:slug>/",
        HowToGuideView.as_view(),
        name="how_to_guide_module",
    ),
]
