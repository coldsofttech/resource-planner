from django.urls import path

from apps.business_units.views import BusinessUnitDetailView, BusinessUnitListView

urlpatterns = [
    path("bu/", BusinessUnitListView.as_view(), name="business-units-list"),
    path(
        "bu/<str:code>/",
        BusinessUnitDetailView.as_view(),
        name="business-units-detail",
    ),
]
