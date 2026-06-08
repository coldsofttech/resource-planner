from django.urls import path

from apps.users.views import MembersView, ProfileView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("members/", MembersView.as_view(), name="members"),
]
