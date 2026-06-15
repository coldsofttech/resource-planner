from django.urls import path

from apps.users.views import (
    GroupDetailView,
    GroupsAdminView,
    MembersView,
    ProfileView,
    UserDetailView,
    UsersAdminView,
)

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("members/", MembersView.as_view(), name="members"),
    path("users/", UsersAdminView.as_view(), name="users-admin"),
    path("users/<str:code>/", UserDetailView.as_view(), name="users-detail"),
    path("groups/", GroupsAdminView.as_view(), name="groups-admin"),
    path("groups/<str:code>/", GroupDetailView.as_view(), name="groups-detail"),
]
