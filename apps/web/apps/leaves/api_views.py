from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.leaves.serializers import (
    LeaveCreateSerializer,
    LeaveDetailSerializer,
    LeaveListSerializer,
    LeaveUpdateSerializer,
)
from apps.leaves.services import (
    LeaveExportService,
    LeaveImportService,
    LeaveService,
)


class LeaveViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = LeaveService
    import_service_class = LeaveImportService
    export_service_class = LeaveExportService

    import_fields = [
        {
            "name": "member_code",
            "type": "string",
            "required": True,
            "description": "Member code (e.g. MBR-1).",
        },
        {
            "name": "start_date",
            "type": "string",
            "required": True,
            "description": "Leave start date in YYYY-MM-DD format.",
        },
        {
            "name": "end_date",
            "type": "string",
            "required": True,
            "description": "Leave end date in YYYY-MM-DD format.",
        },
        {
            "name": "is_half_day",
            "type": "boolean",
            "required": False,
            "description": (
                "Whether this is a half-day leave (true/false). Defaults to false."
            ),
        },
        {
            "name": "half_day_period",
            "type": "string",
            "required": False,
            "description": (
                "Half-day period: AM (Morning) or PM (Afternoon). "
                "Only used when is_half_day is true."
            ),
        },
        {
            "name": "note",
            "type": "string",
            "required": False,
            "description": "Optional note for the leave.",
        },
    ]
    import_notes = [
        "The first row must be a header row.",
        "The 'member_code', 'start_date', and 'end_date' columns are required.",
        "Dates must be in YYYY-MM-DD format.",
        "For half-day leaves, start_date must equal end_date.",
        "Rows that overlap with existing leaves are skipped and reported.",
        f"Maximum {LeaveImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {LeaveImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "leaves_import_template.csv"

    export_columns = [
        {"key": "code", "label": "Code", "default": True},
        {"key": "member", "label": "Member", "default": True},
        {"key": "start_date", "label": "Start Date", "default": True},
        {"key": "end_date", "label": "End Date", "default": True},
        {"key": "is_half_day", "label": "Half Day", "default": True},
        {"key": "half_day_period", "label": "Period", "default": True},
        {"key": "days", "label": "Days", "default": True},
        {"key": "note", "label": "Note", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["MBR-1", "2025-01-06", "2025-01-10", "false", "", "Annual leave"]

    def get_permissions(self):
        action_perms = {
            "list": "leaves.view_leave",
            "retrieve": "leaves.view_leave",
            "create": "leaves.add_leave",
            "partial_update": "leaves.change_leave",
            "destroy": "leaves.delete_leave",
            "statistics": "leaves.view_leave",
            "import_specs": "leaves.import_leave",
            "import_sample": "leaves.import_leave",
            "import_bulk": "leaves.import_leave",
            "export_specs": "leaves.export_leave",
            "export": "leaves.export_leave",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return LeaveListSerializer

    def get_retrieve_serializer_class(self):
        return LeaveDetailSerializer

    def get_create_serializer_class(self):
        return LeaveCreateSerializer

    def get_update_serializer_class(self):
        return LeaveUpdateSerializer

    def get_create_response_serializer_class(self):
        return LeaveDetailSerializer

    @extend_schema(
        summary="List leaves",
        description=(
            "Returns a paginated list of leaves. "
            "Supports filtering by `member` (code) and `is_half_day`."
        ),
        responses={200: LeaveListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /leaves/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a leave",
        responses={
            200: LeaveDetailSerializer,
            404: OpenApiResponse(description="Leave not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /leaves/<code>/"""
        obj = self.service.get(code=code)
        serializer = LeaveDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a leave",
        request=LeaveCreateSerializer,
        responses={
            201: LeaveDetailSerializer,
            409: OpenApiResponse(
                description="An overlapping leave already exists for this member."
            ),
        },
    )
    def create(self, request: Request):
        """POST /leaves/"""
        return super().create(request)

    @extend_schema(
        summary="Update a leave",
        request=LeaveUpdateSerializer,
        responses={
            200: LeaveDetailSerializer,
            404: OpenApiResponse(description="Leave not found."),
            409: OpenApiResponse(
                description="An overlapping leave already exists for this member."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /leaves/<code>/"""
        serializer = LeaveUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        leave = self.service.update(code=code, **serializer.validated_data)
        data = LeaveDetailSerializer(leave, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a leave",
        responses={
            204: OpenApiResponse(description="Leave deleted successfully."),
            404: OpenApiResponse(description="Leave not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /leaves/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )
