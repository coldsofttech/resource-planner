from django.urls import path

from apps.roles.api_views import RoleViewSet

urlpatterns = [
    path(
        "roles/",
        RoleViewSet.as_view({"get": "list", "post": "create"}),
        name="roles-list",
    ),
    path(
        "roles/stats/",
        RoleViewSet.as_view({"get": "statistics"}),
        name="roles-stats",
    ),
    # Options — must precede roles/<code>/ to avoid <code> matching "options"
    path(
        "roles/options/",
        RoleViewSet.as_view({"get": "options"}),
        name="roles-options",
    ),
    # Import — must precede roles/<code>/ to avoid <code> matching "import"
    path(
        "roles/import/specs/",
        RoleViewSet.as_view({"get": "import_specs"}),
        name="roles-import-specs",
    ),
    path(
        "roles/import/sample/",
        RoleViewSet.as_view({"get": "import_sample"}),
        name="roles-import-sample",
    ),
    path(
        "roles/import/",
        RoleViewSet.as_view({"post": "import_bulk"}),
        name="roles-import",
    ),
    # Export — specs must precede export/ to avoid prefix clash
    path(
        "roles/export/specs/",
        RoleViewSet.as_view({"get": "export_specs"}),
        name="roles-export-specs",
    ),
    path(
        "roles/export/",
        RoleViewSet.as_view({"get": "export"}),
        name="roles-export",
    ),
    path(
        "roles/<str:code>/",
        RoleViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="roles-detail",
    ),
    path(
        "roles/<str:code>/activate/",
        RoleViewSet.as_view({"post": "activate"}),
        name="roles-activate",
    ),
    path(
        "roles/<str:code>/deactivate/",
        RoleViewSet.as_view({"post": "deactivate"}),
        name="roles-deactivate",
    ),
    path(
        "roles/<str:code>/set-default/",
        RoleViewSet.as_view({"post": "set_default"}),
        name="roles-set-default",
    ),
    path(
        "roles/<str:code>/members/",
        RoleViewSet.as_view({"get": "members"}),
        name="roles-members",
    ),
]
