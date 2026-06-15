from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.business_units.serializers import (
    BusinessUnitCreateSerializer,
    BusinessUnitDetailSerializer,
    BusinessUnitListSerializer,
    BusinessUnitUpdateSerializer,
)
from apps.business_units.services import (
    BusinessUnitExportService,
    BusinessUnitImportService,
    BusinessUnitService,
)
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin


@extend_schema(tags=["Business Units"])
class BusinessUnitViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = BusinessUnitService
    import_service_class = BusinessUnitImportService
    export_service_class = BusinessUnitExportService

    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "Business unit name (max 255 chars).",
        },
        {
            "name": "short_name",
            "type": "string",
            "required": True,
            "description": "Short name abbreviation (max 10 chars).",
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
        "The 'name' and 'short_name' columns are required.",
        "Rows with duplicate names are skipped and reported in errors.",
        f"Maximum {BusinessUnitImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {BusinessUnitImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "business_units_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "short_name", "label": "Short Name", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Finance", "FIN", "true"]

    def get_permissions(self):
        action_perms = {
            "list": "business_units.view_businessunit",
            "retrieve": "business_units.view_businessunit",
            "create": "business_units.add_businessunit",
            "partial_update": "business_units.change_businessunit",
            "destroy": "business_units.delete_businessunit",
            "activate": "business_units.change_businessunit",
            "deactivate": "business_units.change_businessunit",
            "statistics": "business_units.view_businessunit",
            "options": "business_units.view_businessunit",
            "import_specs": "business_units.import_businessunit",
            "import_sample": "business_units.import_businessunit",
            "import_bulk": "business_units.import_businessunit",
            "export_specs": "business_units.export_businessunit",
            "export": "business_units.export_businessunit",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return BusinessUnitListSerializer

    def get_retrieve_serializer_class(self):
        return BusinessUnitDetailSerializer

    def get_create_serializer_class(self):
        return BusinessUnitCreateSerializer

    def get_update_serializer_class(self):
        return BusinessUnitUpdateSerializer

    def get_create_response_serializer_class(self):
        return BusinessUnitDetailSerializer

    @extend_schema(
        summary="List business unit options",
        description=(
            "Returns a lightweight list of active business units (code + name) "
            "for use in picker fields."
        ),
        responses={
            200: OpenApiResponse(description="List of active business unit options.")
        },
    )
    @action(detail=False, methods=["get"], url_path="options")
    def options(self, request: Request):
        """GET /bu/options/"""
        return self.response(
            data=self.service.options(),
            message="Business unit options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List business units",
        description=(
            "Returns a paginated list of business units. "
            "Defaults to active only. Pass `is_active=false` for inactive. "
            "Supports `search` by name/short_name and `ordering`."
        ),
        responses={200: BusinessUnitListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /bu/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a business unit",
        responses={
            200: BusinessUnitDetailSerializer,
            404: OpenApiResponse(description="Business unit not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /bu/<code>/"""
        obj = self.service.get(code=code)
        serializer = BusinessUnitDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a business unit",
        request=BusinessUnitCreateSerializer,
        responses={
            201: BusinessUnitDetailSerializer,
            409: OpenApiResponse(
                description="A business unit with this name already exists."
            ),
        },
    )
    def create(self, request: Request):
        """POST /bu/"""
        return super().create(request)

    @extend_schema(
        summary="Update a business unit",
        request=BusinessUnitUpdateSerializer,
        responses={
            200: BusinessUnitDetailSerializer,
            404: OpenApiResponse(description="Business unit not found."),
            409: OpenApiResponse(
                description="A business unit with this name already exists."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /bu/<code>/"""
        serializer = BusinessUnitUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        bu = self.service.update(code=code, **serializer.validated_data)
        data = BusinessUnitDetailSerializer(
            bu, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a business unit",
        responses={
            204: OpenApiResponse(description="Business unit deleted successfully."),
            404: OpenApiResponse(description="Business unit not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /bu/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a business unit",
        responses={
            200: BusinessUnitDetailSerializer,
            404: OpenApiResponse(description="Business unit not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /bu/<code>/activate/"""
        bu = self.service.activate(code=code)
        data = BusinessUnitDetailSerializer(
            bu, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a business unit",
        responses={
            200: BusinessUnitDetailSerializer,
            404: OpenApiResponse(description="Business unit not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /bu/<code>/deactivate/"""
        bu = self.service.deactivate(code=code)
        data = BusinessUnitDetailSerializer(
            bu, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )
