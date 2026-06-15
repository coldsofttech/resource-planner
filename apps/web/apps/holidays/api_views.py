from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.holidays.serializers import (
    HolidayCreateSerializer,
    HolidayDetailSerializer,
    HolidayListSerializer,
    HolidayUpdateSerializer,
)
from apps.holidays.services import (
    HolidayExportService,
    HolidayImportService,
    HolidayService,
)


@extend_schema(tags=["Holidays"])
class HolidayViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = HolidayService
    import_service_class = HolidayImportService
    export_service_class = HolidayExportService

    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "Holiday name (max 120 chars).",
        },
        {
            "name": "date",
            "type": "string",
            "required": True,
            "description": "Holiday date in YYYY-MM-DD format.",
        },
        {
            "name": "location_code",
            "type": "string",
            "required": True,
            "description": "Location code (e.g. LOC-1).",
        },
    ]
    import_notes = [
        "The first row must be a header row.",
        "The 'name', 'date', and 'location_code' columns are required.",
        "Date must be in YYYY-MM-DD format.",
        "Rows with duplicate location/date combinations are skipped and reported.",
        f"Maximum {HolidayImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {HolidayImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "holidays_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Name", "default": True},
        {"key": "date", "label": "Date", "default": True},
        {"key": "location", "label": "Location", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Christmas Day", "2025-12-25", "LOC-1"]

    def get_permissions(self):
        action_perms = {
            "list": "holidays.view_holiday",
            "retrieve": "holidays.view_holiday",
            "options": "holidays.view_holiday",
            "create": "holidays.add_holiday",
            "partial_update": "holidays.change_holiday",
            "destroy": "holidays.delete_holiday",
            "statistics": "holidays.view_holiday",
            "import_specs": "holidays.import_holiday",
            "import_sample": "holidays.import_holiday",
            "import_bulk": "holidays.import_holiday",
            "export_specs": "holidays.export_holiday",
            "export": "holidays.export_holiday",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return HolidayListSerializer

    def get_retrieve_serializer_class(self):
        return HolidayDetailSerializer

    def get_create_serializer_class(self):
        return HolidayCreateSerializer

    def get_update_serializer_class(self):
        return HolidayUpdateSerializer

    def get_create_response_serializer_class(self):
        return HolidayDetailSerializer

    @extend_schema(
        summary="List holiday options",
        description=(
            "Returns a lightweight list of holidays (code + name + date + location) "
            "for use in picker fields."
        ),
        responses={200: OpenApiResponse(description="List of holiday options.")},
    )
    def options(self, request: Request):
        """GET /holidays/options/"""
        return self.response(
            data=self.service.options(),
            message="Holiday options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List holidays",
        description=(
            "Returns a paginated list of holidays. "
            "Supports filtering by `location` (code) and `search` by name."
        ),
        responses={200: HolidayListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /holidays/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a holiday",
        responses={
            200: HolidayDetailSerializer,
            404: OpenApiResponse(description="Holiday not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /holidays/<code>/"""
        obj = self.service.get(code=code)
        serializer = HolidayDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a holiday",
        request=HolidayCreateSerializer,
        responses={
            201: HolidayDetailSerializer,
            409: OpenApiResponse(
                description="A holiday for this location on this date already exists."
            ),
        },
    )
    def create(self, request: Request):
        """POST /holidays/"""
        return super().create(request)

    @extend_schema(
        summary="Update a holiday",
        request=HolidayUpdateSerializer,
        responses={
            200: HolidayDetailSerializer,
            404: OpenApiResponse(description="Holiday not found."),
            409: OpenApiResponse(
                description="A holiday for this location on this date already exists."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /holidays/<code>/"""
        serializer = HolidayUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        holiday = self.service.update(code=code, **serializer.validated_data)
        data = HolidayDetailSerializer(
            holiday, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a holiday",
        responses={
            204: OpenApiResponse(description="Holiday deleted successfully."),
            404: OpenApiResponse(description="Holiday not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /holidays/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )
