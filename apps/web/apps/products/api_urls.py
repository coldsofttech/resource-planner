from django.urls import path

from apps.products.api_views import ProductViewSet

urlpatterns = [
    path(
        "products/",
        ProductViewSet.as_view({"get": "list", "post": "create"}),
        name="api-products-list",
    ),
    path(
        "products/stats/",
        ProductViewSet.as_view({"get": "statistics"}),
        name="products-stats",
    ),
    path(
        "products/options/",
        ProductViewSet.as_view({"get": "options"}),
        name="products-options",
    ),
    path(
        "products/import/specs/",
        ProductViewSet.as_view({"get": "import_specs"}),
        name="products-import-specs",
    ),
    path(
        "products/import/sample/",
        ProductViewSet.as_view({"get": "import_sample"}),
        name="products-import-sample",
    ),
    path(
        "products/import/",
        ProductViewSet.as_view({"post": "import_bulk"}),
        name="products-import",
    ),
    path(
        "products/export/specs/",
        ProductViewSet.as_view({"get": "export_specs"}),
        name="products-export-specs",
    ),
    path(
        "products/export/",
        ProductViewSet.as_view({"get": "export"}),
        name="products-export",
    ),
    path(
        "products/<str:code>/",
        ProductViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="products-detail",
    ),
    path(
        "products/<str:code>/activate/",
        ProductViewSet.as_view({"post": "activate"}),
        name="products-activate",
    ),
    path(
        "products/<str:code>/deactivate/",
        ProductViewSet.as_view({"post": "deactivate"}),
        name="products-deactivate",
    ),
]
