from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions import NotFoundException
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.financial_years.serializers import (
    FinancialYearCreateSerializer,
    FinancialYearDetailSerializer,
    FinancialYearListSerializer,
    FinancialYearUpdateSerializer,
)
from apps.financial_years.services import (
    FinancialYearExportService,
    FinancialYearImportService,
    FinancialYearService,
)


class FinancialYearViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = FinancialYearService
    import_service_class = FinancialYearImportService
    export_service_class = FinancialYearExportService

    import_fields = [
        {
            "name": "start_date",
            "type": "date",
            "required": True,
            "description": "Start date of the financial year (YYYY-MM-DD).",
        },
        {
            "name": "end_date",
            "type": "date",
            "required": True,
            "description": "End date of the financial year (YYYY-MM-DD).",
        },
        {
            "name": "status",
            "type": "string",
            "required": False,
            "description": (
                "in_progress / future / completed / expired — defaults to future."
            ),
        },
        {
            "name": "note",
            "type": "string",
            "required": False,
            "description": "Optional note.",
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
        "start_date and end_date are required; all other columns are optional.",
        "Dates must be in YYYY-MM-DD format.",
        "Rows whose date range overlaps an existing financial year are skipped.",
        f"Maximum {FinancialYearImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {FinancialYearImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "financial_years_import_template.csv"

    export_columns = [
        {"key": "long_fy", "label": "Financial Year (Long)", "default": True},
        {"key": "short_fy", "label": "Financial Year (Short)", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "start_date", "label": "Start Date", "default": True},
        {"key": "end_date", "label": "End Date", "default": True},
        {"key": "span_days", "label": "Span (Days)", "default": True},
        {"key": "status", "label": "Status", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "note", "label": "Note", "default": False},
        {"key": "created_at", "label": "Created On", "default": False},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["2025-04-01", "2026-03-31", "future", "", "true"]

    def get_permissions(self):
        action_perms = {
            "list": "financial_years.view_financialyear",
            "retrieve": "financial_years.view_financialyear",
            "active": "financial_years.view_financialyear",
            "options": "financial_years.view_financialyear",
            "create": "financial_years.add_financialyear",
            "partial_update": "financial_years.change_financialyear",
            "destroy": "financial_years.delete_financialyear",
            "activate": "financial_years.change_financialyear",
            "deactivate": "financial_years.change_financialyear",
            "set_active": "financial_years.change_financialyear",
            "statistics": "financial_years.view_financialyear",
            "import_specs": "financial_years.import_financialyear",
            "import_sample": "financial_years.import_financialyear",
            "import_bulk": "financial_years.import_financialyear",
            "export_specs": "financial_years.export_financialyear",
            "export": "financial_years.export_financialyear",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return FinancialYearListSerializer

    def get_retrieve_serializer_class(self):
        return FinancialYearDetailSerializer

    def get_create_serializer_class(self):
        return FinancialYearCreateSerializer

    def get_update_serializer_class(self):
        return FinancialYearUpdateSerializer

    def get_create_response_serializer_class(self):
        return FinancialYearDetailSerializer

    @extend_schema(
        summary="List financial years",
        description=(
            "Returns a paginated list of financial years. "
            "Defaults to active records. Supports `search`, `status`, and "
            "`is_active` filters."
        ),
        responses={200: FinancialYearListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /fy/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a financial year",
        responses={
            200: FinancialYearDetailSerializer,
            404: OpenApiResponse(description="Financial year not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /fy/<code>/"""
        obj = self.service.get(code=code)
        serializer = FinancialYearDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Get active financial year",
        description="Returns the currently active (In Progress) financial year.",
        responses={
            200: FinancialYearDetailSerializer,
            404: OpenApiResponse(description="No active financial year found."),
        },
    )
    def active(self, request: Request):
        """GET /fy/active/"""
        try:
            obj = self.service.get_active()
        except NotFoundException:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "not_found",
                        "message": "No active financial year found.",
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = FinancialYearDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(
            data=serializer.data,
            message="Active financial year retrieved successfully.",
        )

    @extend_schema(
        summary="Create a financial year",
        request=FinancialYearCreateSerializer,
        responses={
            201: FinancialYearDetailSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def create(self, request: Request):
        """POST /fy/"""
        return super().create(request)

    @extend_schema(
        summary="Update a financial year",
        request=FinancialYearUpdateSerializer,
        responses={
            200: FinancialYearDetailSerializer,
            404: OpenApiResponse(description="Financial year not found."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /fy/<code>/"""
        serializer = FinancialYearUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = FinancialYearDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a financial year",
        responses={
            204: OpenApiResponse(description="Financial year deleted successfully."),
            404: OpenApiResponse(description="Financial year not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /fy/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a financial year record",
        responses={
            200: FinancialYearDetailSerializer,
            404: OpenApiResponse(description="Financial year not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /fy/<code>/activate/"""
        obj = self.service.activate(code=code)
        data = FinancialYearDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message=self.get_activate_custom_message())

    @extend_schema(
        summary="Deactivate a financial year record",
        responses={
            200: FinancialYearDetailSerializer,
            404: OpenApiResponse(description="Financial year not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /fy/<code>/deactivate/"""
        obj = self.service.deactivate(code=code)
        data = FinancialYearDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message=self.get_deactivate_custom_message())

    @extend_schema(
        summary="Set financial year status to In Progress",
        description="Changes the financial year's status to 'in_progress' (active).",
        responses={
            200: FinancialYearDetailSerializer,
            404: OpenApiResponse(description="Financial year not found."),
        },
    )
    def set_active(self, request: Request, code=None):
        """POST /fy/<code>/set-active/"""
        obj = self.service.set_active(code=code)
        data = FinancialYearDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message="Financial year set to In Progress.",
        )

    @extend_schema(
        summary="List financial year options",
        description=(
            "Returns a lightweight list of active financial years for picker fields."
        ),
        responses={200: OpenApiResponse(description="List of financial year options.")},
    )
    def options(self, request: Request):
        """GET /fy/options/"""
        return self.response(
            data=self.service.options(),
            message="Financial year options retrieved successfully.",
        )
