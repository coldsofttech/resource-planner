from django.urls import path

from apps.recharges.views import RechargeTypeDetailView, RechargeTypesListView

urlpatterns = [
    path(
        "recharges/types/", RechargeTypesListView.as_view(), name="recharge-types-list"
    ),
    path(
        "recharges/types/<str:code>/",
        RechargeTypeDetailView.as_view(),
        name="recharge-type-detail",
    ),
]
