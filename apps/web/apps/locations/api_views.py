from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.locations.serializers import (
    LocationCreateSerializer,
    LocationDetailSerializer,
    LocationListSerializer,
    LocationUpdateSerializer,
)
from apps.locations.services import (
    LocationExportService,
    LocationImportService,
    LocationService,
)
from apps.users.serializers import MemberMiniListSerializer
from apps.users.services import MembersService


class LocationViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = LocationService
    import_service_class = LocationImportService
    export_service_class = LocationExportService

    # Import metadata surfaced via GET /locations/import/specs/
    import_fields = [
        {
            "name": "city",
            "type": "string",
            "required": True,
            "description": "City name (max 100 chars).",
        },
        {
            "name": "country",
            "type": "string",
            "required": True,
            "description": "Country name (max 100 chars).",
        },
        {
            "name": "is_active",
            "type": "boolean",
            "required": False,
            "description": "true/false/yes/no/1/0 — defaults to true.",
        },
        {
            "name": "is_default",
            "type": "boolean",
            "required": False,
            "description": "true/false/yes/no/1/0 — defaults to false.",
        },
    ]
    import_notes = [
        "The first row must be a header row.",
        "The 'city' and 'country' columns are required; all other columns are "
        "optional.",
        "Rows with duplicate city/country combinations are skipped and reported in "
        "errors.",
        f"Maximum {LocationImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {LocationImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "locations_import_template.csv"

    # Export column specs surfaced via GET /locations/export/specs/
    export_columns = [
        {"key": "city", "label": "City", "default": True},
        {"key": "country", "label": "Country", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "is_default", "label": "Default", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["London", "United Kingdom", "true", "false"]

    def get_permissions(self):
        action_perms = {
            "list": "locations.view_location",
            "retrieve": "locations.view_location",
            "options": "locations.view_location",
            "create": "locations.add_location",
            "partial_update": "locations.change_location",
            "destroy": "locations.delete_location",
            "activate": "locations.change_location",
            "deactivate": "locations.change_location",
            "set_default": "locations.change_location",
            "statistics": "locations.view_location",
            "import_specs": "locations.import_location",
            "import_sample": "locations.import_location",
            "import_bulk": "locations.import_location",
            "export_specs": "locations.export_location",
            "export": "locations.export_location",
            "members": "locations.view_location",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return LocationListSerializer

    def get_retrieve_serializer_class(self):
        return LocationDetailSerializer

    def get_create_serializer_class(self):
        return LocationCreateSerializer

    def get_update_serializer_class(self):
        return LocationUpdateSerializer

    def get_create_response_serializer_class(self):
        return LocationDetailSerializer

    @extend_schema(
        summary="List location options",
        description=(
            "Returns a lightweight list of active locations (code + city + country) "
            "for use in picker fields."
        ),
        responses={
            200: OpenApiResponse(description="List of active location options.")
        },
    )
    def options(self, request: Request):
        """GET /locations/options/"""
        return self.response(
            data=self.service.options(),
            message="Location options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List locations",
        description=(
            "Returns a paginated list of locations. "
            "Defaults to active locations only. Pass `is_active=false` to list "
            "inactive locations. Supports `search` by city or country."
        ),
        responses={200: LocationListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /locations/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a location",
        responses={
            200: LocationDetailSerializer,
            404: OpenApiResponse(description="Location not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /locations/<code>/"""
        obj = self.service.get(code=code)
        serializer = LocationDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a location",
        request=LocationCreateSerializer,
        responses={
            201: LocationDetailSerializer,
            409: OpenApiResponse(
                description=(
                    "A location with this city/country combination already exists."
                )
            ),
        },
    )
    def create(self, request: Request):
        """POST /locations/"""
        return super().create(request)

    @extend_schema(
        summary="Update a location",
        request=LocationUpdateSerializer,
        responses={
            200: LocationDetailSerializer,
            404: OpenApiResponse(description="Location not found."),
            409: OpenApiResponse(
                description=(
                    "A location with this city/country combination already exists."
                )
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /locations/<code>/"""
        serializer = LocationUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        location = self.service.update(code=code, **serializer.validated_data)
        data = LocationDetailSerializer(
            location, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a location",
        responses={
            204: OpenApiResponse(description="Location deleted successfully."),
            404: OpenApiResponse(description="Location not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /locations/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a location",
        responses={
            200: LocationDetailSerializer,
            404: OpenApiResponse(description="Location not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /locations/<code>/activate/"""
        location = self.service.activate(code=code)
        data = LocationDetailSerializer(
            location, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a location",
        responses={
            200: LocationDetailSerializer,
            404: OpenApiResponse(description="Location not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /locations/<code>/deactivate/"""
        location = self.service.deactivate(code=code)
        data = LocationDetailSerializer(
            location, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )

    @extend_schema(
        summary="Set a location as default",
        responses={
            200: LocationDetailSerializer,
            404: OpenApiResponse(description="Location not found."),
        },
    )
    def set_default(self, request: Request, code=None):
        """POST /locations/<code>/set-default/"""
        location = self.service.set_default(code=code)
        data = LocationDetailSerializer(
            location, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_set_default_custom_message(),
            status_code=self.get_set_default_status_code(),
        )

    @extend_schema(
        summary="List location members",
        description="Returns a paginated list of members based at this location.",
        responses={
            200: MemberMiniListSerializer(many=True),
            404: OpenApiResponse(description="Location not found."),
        },
    )
    def members(self, request: Request, code=None):
        """GET /locations/<code>/members/"""
        self.service.get(code=code)
        svc = MembersService(user=request.user, request=request)
        params = self.get_list_params(request)
        params.filters["location"] = code
        result = svc.list(params=params)
        return self.paginated_response(
            result=result,
            serializer_class=MemberMiniListSerializer,
        )
