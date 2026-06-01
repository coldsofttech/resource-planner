from django.urls import path

from apps.permissions.api_views import (
    GroupPermissionCategoryViewSet,
    PermissionCategoryViewSet,
    UserPermissionCategoryViewSet,
)

urlpatterns = [
    path(
        "permissions/categories/",
        PermissionCategoryViewSet.as_view({"get": "list"}),
        name="permissions-categories-list",
    ),
    path(
        "permissions/categories/<str:code>/",
        PermissionCategoryViewSet.as_view({"get": "retrieve"}),
        name="permissions-categories-detail",
    ),
    path(
        "permissions/groups/<str:group_code>/",
        GroupPermissionCategoryViewSet.as_view({"get": "list", "post": "create"}),
        name="permissions-groups-list",
    ),
    path(
        "permissions/groups/<str:group_code>/<str:code>/",
        GroupPermissionCategoryViewSet.as_view(
            {"patch": "partial_update", "delete": "destroy"}
        ),
        name="permissions-groups-detail",
    ),
    path(
        "permissions/users/<str:user_code>/",
        UserPermissionCategoryViewSet.as_view({"get": "list", "post": "create"}),
        name="permissions-users-list",
    ),
    path(
        "permissions/users/<str:user_code>/effective/",
        UserPermissionCategoryViewSet.as_view({"get": "effective"}),
        name="permissions-users-effective",
    ),
    path(
        "permissions/users/<str:user_code>/<str:code>/",
        UserPermissionCategoryViewSet.as_view(
            {"patch": "partial_update", "delete": "destroy"}
        ),
        name="permissions-users-detail",
    ),
]
