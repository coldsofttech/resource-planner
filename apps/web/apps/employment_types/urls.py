from django.urls import path

from apps.employment_types.views import EmploymentTypesListView

urlpatterns = [
    path("emp-types/", EmploymentTypesListView.as_view(), name="emp-types-list"),
]
