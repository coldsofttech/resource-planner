from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.roles.serializers import (
    RoleCreateSerializer,
    RoleDetailSerializer,
    RoleListSerializer,
    RoleUpdateSerializer,
)
from apps.roles.services import (
    RoleExportService,
    RoleImportService,
    RoleService,
)


class RoleViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = RoleService
    import_service_class = RoleImportService
    export_service_class = RoleExportService

    # Import metadata surfaced via GET /roles/import/specs/
    import_fields = [
        {
            "name": "role",
            "type": "string",
            "required": True,
            "description": "Role name (max 100 chars, must be unique).",
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
        {
            "name": "is_assignable",
            "type": "boolean",
            "required": False,
            "description": "true/false/yes/no/1/0 — defaults to false.",
        },
        {
            "name": "is_leadership",
            "type": "boolean",
            "required": False,
            "description": "true/false/yes/no/1/0 — defaults to false.",
        },
    ]
    import_notes = [
        "The first row must be a header row.",
        "The 'role' column is required; all other columns are optional.",
        "Rows with duplicate role names are skipped and reported in errors.",
        f"Maximum {RoleImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {RoleImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "roles_import_template.csv"

    # Export column specs surfaced via GET /roles/export/specs/
    export_columns = [
        {"key": "role", "label": "Role Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "is_default", "label": "Default", "default": True},
        {"key": "is_assignable", "label": "Assignable", "default": True},
        {"key": "is_leadership", "label": "Leadership", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Developer", "true", "false", "true", "false"]

    def get_permissions(self):
        action_perms = {
            "list": "roles.view_role",
            "retrieve": "roles.view_role",
            "options": "roles.view_role",
            "create": "roles.add_role",
            "partial_update": "roles.change_role",
            "destroy": "roles.delete_role",
            "activate": "roles.change_role",
            "deactivate": "roles.change_role",
            "set_default": "roles.change_role",
            "statistics": "roles.view_role",
            "import_specs": "roles.import_role",
            "import_sample": "roles.import_role",
            "import_bulk": "roles.import_role",
            "export_specs": "roles.export_role",
            "export": "roles.export_role",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return RoleListSerializer

    def get_retrieve_serializer_class(self):
        return RoleDetailSerializer

    def get_create_serializer_class(self):
        return RoleCreateSerializer

    def get_update_serializer_class(self):
        return RoleUpdateSerializer

    def get_create_response_serializer_class(self):
        return RoleDetailSerializer

    @extend_schema(
        summary="List role options",
        description=(
            "Returns a lightweight list of active roles (code + role name) for use in "
            "picker fields."
        ),
        responses={200: OpenApiResponse(description="List of active role options.")},
    )
    def options(self, request: Request):
        """GET /roles/options/"""
        return self.response(
            data=self.service.options(),
            message="Role options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List roles",
        description=(
            "Returns a paginated list of roles. "
            "Defaults to active roles only. Pass `is_active=false` to list "
            "inactive roles. Supports `search` by role name."
        ),
        responses={200: RoleListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /roles/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a role",
        responses={
            200: RoleDetailSerializer,
            404: OpenApiResponse(description="Role not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /roles/<code>/"""
        obj = self.service.get(code=code)
        serializer = RoleDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a role",
        request=RoleCreateSerializer,
        responses={
            201: RoleDetailSerializer,
            409: OpenApiResponse(description="A role with this name already exists."),
        },
    )
    def create(self, request: Request):
        """POST /roles/"""
        return super().create(request)

    @extend_schema(
        summary="Update a role",
        request=RoleUpdateSerializer,
        responses={
            200: RoleDetailSerializer,
            404: OpenApiResponse(description="Role not found."),
            409: OpenApiResponse(description="A role with this name already exists."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /roles/<code>/"""
        serializer = RoleUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = RoleDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a role",
        responses={
            204: OpenApiResponse(description="Role deleted successfully."),
            404: OpenApiResponse(description="Role not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /roles/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a role",
        responses={
            200: RoleDetailSerializer,
            404: OpenApiResponse(description="Role not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /roles/<code>/activate/"""
        obj = self.service.activate(code=code)
        data = RoleDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a role",
        responses={
            200: RoleDetailSerializer,
            404: OpenApiResponse(description="Role not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /roles/<code>/deactivate/"""
        obj = self.service.deactivate(code=code)
        data = RoleDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )

    @extend_schema(
        summary="Set a role as default",
        responses={
            200: RoleDetailSerializer,
            404: OpenApiResponse(description="Role not found."),
        },
    )
    def set_default(self, request: Request, code=None):
        """POST /roles/<code>/set-default/"""
        obj = self.service.set_default(code=code)
        data = RoleDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_set_default_custom_message(),
            status_code=self.get_set_default_status_code(),
        )
