from django.urls import path

from apps.recharges.views import (
    RechargeDetailView,
    RechargeEmailReviewView,
    RechargeProjectGroupsListView,
    RechargesView,
    RechargeTypeDetailView,
    RechargeTypesListView,
)

urlpatterns = [
    path("recharges/", RechargesView.as_view(), name="recharges"),
    path(
        "recharges/project-groups/",
        RechargeProjectGroupsListView.as_view(),
        name="recharge-project-groups",
    ),
    path(
        "recharges/types/", RechargeTypesListView.as_view(), name="recharge-types-list"
    ),
    path(
        "recharges/types/<str:code>/",
        RechargeTypeDetailView.as_view(),
        name="recharge-type-detail",
    ),
    path(
        "recharges/<str:sprint_code>/forecasts/",
        RechargeEmailReviewView.as_view(),
        name="recharge-email-review-forecasts",
        kwargs={"review_type": "forecast"},
    ),
    path(
        "recharges/<str:sprint_code>/actuals/",
        RechargeEmailReviewView.as_view(),
        name="recharge-email-review-actuals",
        kwargs={"review_type": "actual"},
    ),
    path(
        "recharges/<str:code>/",
        RechargeDetailView.as_view(),
        name="recharge-detail",
    ),
]
