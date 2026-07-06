from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request

from apps.auth.authentication import BearerTokenAuthentication
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.products.serializers import (
    ProductCreateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductUpdateSerializer,
)
from apps.products.services import (
    ProductExportService,
    ProductImportService,
    ProductService,
)


@extend_schema(tags=["Products"])
class ProductViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = ProductService
    import_service_class = ProductImportService
    export_service_class = ProductExportService

    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "Product name (max 255 chars).",
        },
        {
            "name": "short_name",
            "type": "string",
            "required": True,
            "description": "Short name abbreviation (max 10 chars).",
        },
        {
            "name": "business_unit_code",
            "type": "string",
            "required": True,
            "description": "Business unit code (e.g. BU-1).",
        },
        {
            "name": "is_active",
            "type": "boolean",
            "required": False,
            "description": "true/false/yes/no/1/0 — defaults to true.",
        },
    ]
    import_notes = [
        "The first row must be a header row.",
        "The 'name', 'short_name', and 'business_unit_code' columns are required.",
        "Rows with duplicate names within the same business unit are skipped.",
        f"Maximum {ProductImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {ProductImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "products_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "short_name", "label": "Short Name", "default": True},
        {"key": "business_unit", "label": "Business Unit", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Core Platform", "CP", "BU-1", "true"]

    def get_authenticators(self):
        if "options" in getattr(self, "action_map", {}).values():
            return []
        from rest_framework.authentication import SessionAuthentication

        return [BearerTokenAuthentication(), SessionAuthentication()]

    def get_permissions(self):
        if self.action == "options":
            return [AllowAny()]
        action_perms = {
            "list": "products.view_product",
            "retrieve": "products.view_product",
            "create": "products.add_product",
            "partial_update": "products.change_product",
            "destroy": "products.delete_product",
            "activate": "products.change_product",
            "deactivate": "products.change_product",
            "statistics": "products.view_product",
            "import_specs": "products.import_product",
            "import_sample": "products.import_product",
            "import_bulk": "products.import_product",
            "export_specs": "products.export_product",
            "export": "products.export_product",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return ProductListSerializer

    def get_retrieve_serializer_class(self):
        return ProductDetailSerializer

    def get_create_serializer_class(self):
        return ProductCreateSerializer

    def get_update_serializer_class(self):
        return ProductUpdateSerializer

    def get_create_response_serializer_class(self):
        return ProductDetailSerializer

    @extend_schema(
        summary="List product options",
        description=(
            "Returns a lightweight list of active products (code + name + "
            "business unit) for use in picker fields."
        ),
        responses={200: OpenApiResponse(description="List of active product options.")},
    )
    @action(detail=False, methods=["get"], url_path="options")
    def options(self, request: Request):
        """GET /products/options/"""
        return self.response(
            data=self.service.options(),
            message="Product options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List products",
        description=(
            "Returns a paginated list of products. "
            "Defaults to active only. Pass `is_active=false` for inactive. "
            "Supports `search` by name/short_name, filter by `bu` "
            "(business unit code), and `ordering`."
        ),
        responses={200: ProductListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /products/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a product",
        responses={
            200: ProductDetailSerializer,
            404: OpenApiResponse(description="Product not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /products/<code>/"""
        obj = self.service.get(code=code)
        serializer = ProductDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a product",
        request=ProductCreateSerializer,
        responses={
            201: ProductDetailSerializer,
            409: OpenApiResponse(
                description=(
                    "A product with this name already exists in the business unit."
                )
            ),
        },
    )
    def create(self, request: Request):
        """POST /products/"""
        return super().create(request)

    @extend_schema(
        summary="Update a product",
        request=ProductUpdateSerializer,
        responses={
            200: ProductDetailSerializer,
            404: OpenApiResponse(description="Product not found."),
            409: OpenApiResponse(
                description=(
                    "A product with this name already exists in the business unit."
                )
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /products/<code>/"""
        serializer = ProductUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        product = self.service.update(code=code, **serializer.validated_data)
        data = ProductDetailSerializer(
            product, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a product",
        responses={
            204: OpenApiResponse(description="Product deleted successfully."),
            404: OpenApiResponse(description="Product not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /products/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a product",
        responses={
            200: ProductDetailSerializer,
            404: OpenApiResponse(description="Product not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /products/<code>/activate/"""
        product = self.service.activate(code=code)
        data = ProductDetailSerializer(
            product, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a product",
        responses={
            200: ProductDetailSerializer,
            404: OpenApiResponse(description="Product not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /products/<code>/deactivate/"""
        product = self.service.deactivate(code=code)
        data = ProductDetailSerializer(
            product, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )
