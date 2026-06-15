from django.urls import path

from apps.tags.api_views import TagViewSet

urlpatterns = [
    path(
        "tags/",
        TagViewSet.as_view({"get": "list", "post": "create"}),
        name="tags-list",
    ),
    path(
        "tags/export/specs/",
        TagViewSet.as_view({"get": "export_specs"}),
        name="tags-export-specs",
    ),
    path(
        "tags/export/",
        TagViewSet.as_view({"get": "export"}),
        name="tags-export",
    ),
]
