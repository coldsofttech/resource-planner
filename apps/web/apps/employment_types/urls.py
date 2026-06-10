from django.urls import path

from apps.employment_types.views import (
    EmploymentTypeDetailView,
    EmploymentTypesListView,
)

urlpatterns = [
    path("emp-types/", EmploymentTypesListView.as_view(), name="emp-types-list"),
    path(
        "emp-types/<str:code>/",
        EmploymentTypeDetailView.as_view(),
        name="emp-types-detail",
    ),
]
