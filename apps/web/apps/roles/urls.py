from django.urls import path

from apps.roles.views import RolesListView

urlpatterns = [
    path("roles/", RolesListView.as_view(), name="roles-list"),
]
