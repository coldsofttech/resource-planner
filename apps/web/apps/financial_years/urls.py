from django.urls import path

from apps.financial_years.views import FinancialYearsListView

urlpatterns = [
    path("fy/", FinancialYearsListView.as_view(), name="fy-list"),
]
