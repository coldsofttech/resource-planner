from django.urls import path

from apps.roles.views import RoleDetailView, RolesListView

urlpatterns = [
    path("roles/", RolesListView.as_view(), name="roles-list"),
    path("roles/<str:code>/", RoleDetailView.as_view(), name="roles-detail"),
]
