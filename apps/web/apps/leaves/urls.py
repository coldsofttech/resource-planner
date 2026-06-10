from django.urls import path

from apps.leaves.views import LeavesListView

urlpatterns = [
    path("leaves/", LeavesListView.as_view(), name="leaves-list"),
]
