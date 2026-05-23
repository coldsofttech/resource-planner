from django.urls import path

from apps.setup.views import SetupView

urlpatterns = [path("", SetupView.as_view(), name="setup-wizard")]
