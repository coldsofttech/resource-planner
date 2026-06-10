from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.employment_types.serializers import (
    EmploymentTypeCreateSerializer,
    EmploymentTypeDetailSerializer,
    EmploymentTypeListSerializer,
    EmploymentTypeUpdateSerializer,
)
from apps.employment_types.services import (
    EmploymentTypeExportService,
    EmploymentTypeImportService,
    EmploymentTypeService,
)
from apps.users.serializers import MemberMiniListSerializer
from apps.users.services import MembersService


class EmploymentTypeViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = EmploymentTypeService
    import_service_class = EmploymentTypeImportService
    export_service_class = EmploymentTypeExportService

    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "Employment type name (max 100 chars).",
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
        "The 'name' column is required; all other columns are optional.",
        "Rows with duplicate names are skipped and reported in errors.",
        f"Maximum {EmploymentTypeImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {EmploymentTypeImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "employment_types_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "is_default", "label": "Default", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Full-time", "true", "false"]

    def get_permissions(self):
        action_perms = {
            "list": "employment_types.view_employmenttype",
            "retrieve": "employment_types.view_employmenttype",
            "options": "employment_types.view_employmenttype",
            "create": "employment_types.add_employmenttype",
            "partial_update": "employment_types.change_employmenttype",
            "destroy": "employment_types.delete_employmenttype",
            "activate": "employment_types.change_employmenttype",
            "deactivate": "employment_types.change_employmenttype",
            "set_default": "employment_types.change_employmenttype",
            "statistics": "employment_types.view_employmenttype",
            "import_specs": "employment_types.import_employmenttype",
            "import_sample": "employment_types.import_employmenttype",
            "import_bulk": "employment_types.import_employmenttype",
            "export_specs": "employment_types.export_employmenttype",
            "export": "employment_types.export_employmenttype",
            "members": "employment_types.view_employmenttype",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return EmploymentTypeListSerializer

    def get_retrieve_serializer_class(self):
        return EmploymentTypeDetailSerializer

    def get_create_serializer_class(self):
        return EmploymentTypeCreateSerializer

    def get_update_serializer_class(self):
        return EmploymentTypeUpdateSerializer

    def get_create_response_serializer_class(self):
        return EmploymentTypeDetailSerializer

    @extend_schema(
        summary="List employment type options",
        description=(
            "Returns a lightweight list of active employment types (code + name) "
            "for use in picker fields."
        ),
        responses={
            200: OpenApiResponse(description="List of active employment type options.")
        },
    )
    def options(self, request: Request):
        """GET /emp-types/options/"""
        return self.response(
            data=self.service.options(),
            message="Employment type options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List employment types",
        description=(
            "Returns a paginated list of employment types. "
            "Defaults to active records only. Pass `is_active=false` to list "
            "inactive records. Supports `search` by name."
        ),
        responses={200: EmploymentTypeListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /emp-types/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve an employment type",
        responses={
            200: EmploymentTypeDetailSerializer,
            404: OpenApiResponse(description="Employment type not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /emp-types/<code>/"""
        obj = self.service.get(code=code)
        serializer = EmploymentTypeDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create an employment type",
        request=EmploymentTypeCreateSerializer,
        responses={
            201: EmploymentTypeDetailSerializer,
            409: OpenApiResponse(
                description="An employment type with this name already exists."
            ),
        },
    )
    def create(self, request: Request):
        """POST /emp-types/"""
        return super().create(request)

    @extend_schema(
        summary="Update an employment type",
        request=EmploymentTypeUpdateSerializer,
        responses={
            200: EmploymentTypeDetailSerializer,
            404: OpenApiResponse(description="Employment type not found."),
            409: OpenApiResponse(
                description="An employment type with this name already exists."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /emp-types/<code>/"""
        serializer = EmploymentTypeUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        employment_type = self.service.update(code=code, **serializer.validated_data)
        data = EmploymentTypeDetailSerializer(
            employment_type, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete an employment type",
        responses={
            204: OpenApiResponse(description="Employment type deleted successfully."),
            404: OpenApiResponse(description="Employment type not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /emp-types/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate an employment type",
        responses={
            200: EmploymentTypeDetailSerializer,
            404: OpenApiResponse(description="Employment type not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /emp-types/<code>/activate/"""
        employment_type = self.service.activate(code=code)
        data = EmploymentTypeDetailSerializer(
            employment_type, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate an employment type",
        responses={
            200: EmploymentTypeDetailSerializer,
            404: OpenApiResponse(description="Employment type not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /emp-types/<code>/deactivate/"""
        employment_type = self.service.deactivate(code=code)
        data = EmploymentTypeDetailSerializer(
            employment_type, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )

    @extend_schema(
        summary="Set an employment type as default",
        responses={
            200: EmploymentTypeDetailSerializer,
            404: OpenApiResponse(description="Employment type not found."),
        },
    )
    def set_default(self, request: Request, code=None):
        """POST /emp-types/<code>/set-default/"""
        employment_type = self.service.set_default(code=code)
        data = EmploymentTypeDetailSerializer(
            employment_type, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_set_default_custom_message(),
            status_code=self.get_set_default_status_code(),
        )

    @extend_schema(
        summary="List employment type members",
        description="Returns a paginated list of members with this employment type.",
        responses={
            200: MemberMiniListSerializer(many=True),
            404: OpenApiResponse(description="Employment type not found."),
        },
    )
    def members(self, request: Request, code=None):
        """GET /emp-types/<code>/members/"""
        self.service.get(code=code)
        svc = MembersService(user=request.user, request=request)
        params = self.get_list_params(request)
        params.filters["employment_type"] = code
        result = svc.list(params=params)
        return self.paginated_response(
            result=result,
            serializer_class=MemberMiniListSerializer,
        )
