from django.urls import path

from apps.business_units.views import BusinessUnitListView

urlpatterns = [
    path("bu/", BusinessUnitListView.as_view(), name="business-units-list"),
]
