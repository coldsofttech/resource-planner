from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.projects.serializers import (
    ProjectTypeCreateSerializer,
    ProjectTypeDetailSerializer,
    ProjectTypeListSerializer,
    ProjectTypeUpdateSerializer,
)
from apps.projects.services import (
    ProjectTypeExportService,
    ProjectTypeImportService,
    ProjectTypeService,
)


@extend_schema(tags=["Projects: Types"])
class ProjectTypeViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = ProjectTypeService
    import_service_class = ProjectTypeImportService
    export_service_class = ProjectTypeExportService

    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "Project type name (max 60 chars, must be unique).",
        },
        {
            "name": "description",
            "type": "string",
            "required": False,
            "description": "Optional description.",
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
        "The 'name' column is required; all other columns are optional.",
        "Rows with duplicate project type names are skipped and reported in errors.",
        f"Maximum {ProjectTypeImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {ProjectTypeImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "project_types_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Project Type Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "description", "label": "Description", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Internal", "Internal development projects", "true"]

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projecttype",
            "retrieve": "projects.view_projecttype",
            "options": "projects.view_projecttype",
            "statistics": "projects.view_projecttype",
            "create": "projects.add_projecttype",
            "partial_update": "projects.change_projecttype",
            "destroy": "projects.delete_projecttype",
            "activate": "projects.change_projecttype",
            "deactivate": "projects.change_projecttype",
            "import_specs": "projects.import_projecttype",
            "import_sample": "projects.import_projecttype",
            "import_bulk": "projects.import_projecttype",
            "export_specs": "projects.export_projecttype",
            "export": "projects.export_projecttype",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return ProjectTypeListSerializer

    def get_retrieve_serializer_class(self):
        return ProjectTypeDetailSerializer

    def get_create_serializer_class(self):
        return ProjectTypeCreateSerializer

    def get_update_serializer_class(self):
        return ProjectTypeUpdateSerializer

    def get_create_response_serializer_class(self):
        return ProjectTypeDetailSerializer

    @extend_schema(
        summary="List project type options",
        responses={
            200: OpenApiResponse(description="List of active project type options.")
        },
    )
    def options(self, request: Request):
        """GET /projects/types/options/"""
        return self.response(
            data=self.service.options(),
            message="Project type options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List project types",
        responses={200: ProjectTypeListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /projects/types/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a project type",
        responses={
            200: ProjectTypeDetailSerializer,
            404: OpenApiResponse(description="Project type not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /projects/types/<code>/"""
        obj = self.service.get(code=code)
        serializer = ProjectTypeDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a project type",
        request=ProjectTypeCreateSerializer,
        responses={
            201: ProjectTypeDetailSerializer,
            409: OpenApiResponse(
                description="A project type with this name already exists."
            ),
        },
    )
    def create(self, request: Request):
        """POST /projects/types/"""
        return super().create(request)

    @extend_schema(
        summary="Update a project type",
        request=ProjectTypeUpdateSerializer,
        responses={
            200: ProjectTypeDetailSerializer,
            404: OpenApiResponse(description="Project type not found."),
            409: OpenApiResponse(
                description="A project type with this name already exists."
            ),
            422: OpenApiResponse(
                description="Protected project types cannot be modified."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /projects/types/<code>/"""
        serializer = ProjectTypeUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = ProjectTypeDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a project type",
        responses={
            204: OpenApiResponse(description="Project type deleted successfully."),
            404: OpenApiResponse(description="Project type not found."),
            422: OpenApiResponse(
                description="Protected project types cannot be deleted."
            ),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /projects/types/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a project type",
        responses={
            200: ProjectTypeDetailSerializer,
            404: OpenApiResponse(description="Project type not found."),
            422: OpenApiResponse(
                description="Protected project types cannot be modified."
            ),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /projects/types/<code>/activate/"""
        obj = self.service.activate(code=code)
        data = ProjectTypeDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a project type",
        responses={
            200: ProjectTypeDetailSerializer,
            404: OpenApiResponse(description="Project type not found."),
            422: OpenApiResponse(
                description="Protected project types cannot be modified."
            ),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /projects/types/<code>/deactivate/"""
        obj = self.service.deactivate(code=code)
        data = ProjectTypeDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )
