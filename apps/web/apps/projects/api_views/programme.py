from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.projects.serializers import (
    ProgrammeCreateSerializer,
    ProgrammeDetailSerializer,
    ProgrammeListSerializer,
    ProgrammeUpdateSerializer,
)
from apps.projects.services import (
    ProgrammeExportService,
    ProgrammeImportService,
    ProgrammeService,
)


@extend_schema(tags=["Programmes"])
class ProgrammeViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = ProgrammeService
    import_service_class = ProgrammeImportService
    export_service_class = ProgrammeExportService

    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "Programme name (max 255 chars, must be unique).",
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
        "Rows with duplicate programme names are skipped and reported in errors.",
        "Protected programmes (e.g. 'Others') cannot be imported as duplicates.",
        f"Maximum {ProgrammeImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {ProgrammeImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "programmes_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Programme Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "description", "label": "Description", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Digital Transformation", "Strategic digital initiatives", "true"]

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_programme",
            "retrieve": "projects.view_programme",
            "options": "projects.view_programme",
            "statistics": "projects.view_programme",
            "create": "projects.add_programme",
            "partial_update": "projects.change_programme",
            "destroy": "projects.delete_programme",
            "activate": "projects.change_programme",
            "deactivate": "projects.change_programme",
            "import_specs": "projects.import_programme",
            "import_sample": "projects.import_programme",
            "import_bulk": "projects.import_programme",
            "export_specs": "projects.export_programme",
            "export": "projects.export_programme",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return ProgrammeListSerializer

    def get_retrieve_serializer_class(self):
        return ProgrammeDetailSerializer

    def get_create_serializer_class(self):
        return ProgrammeCreateSerializer

    def get_update_serializer_class(self):
        return ProgrammeUpdateSerializer

    def get_create_response_serializer_class(self):
        return ProgrammeDetailSerializer

    @extend_schema(
        summary="List programme options",
        responses={
            200: OpenApiResponse(description="List of active programme options.")
        },
    )
    def options(self, request: Request):
        """GET /programmes/options/"""
        return self.response(
            data=self.service.options(),
            message="Programme options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List programmes",
        responses={200: ProgrammeListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /programmes/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a programme",
        responses={
            200: ProgrammeDetailSerializer,
            404: OpenApiResponse(description="Programme not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /programmes/<code>/"""
        obj = self.service.get(code=code)
        serializer = ProgrammeDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a programme",
        request=ProgrammeCreateSerializer,
        responses={
            201: ProgrammeDetailSerializer,
            409: OpenApiResponse(
                description="A programme with this name already exists."
            ),
        },
    )
    def create(self, request: Request):
        """POST /programmes/"""
        return super().create(request)

    @extend_schema(
        summary="Update a programme",
        request=ProgrammeUpdateSerializer,
        responses={
            200: ProgrammeDetailSerializer,
            404: OpenApiResponse(description="Programme not found."),
            409: OpenApiResponse(
                description="A programme with this name already exists."
            ),
            422: OpenApiResponse(
                description="Protected programmes cannot be modified."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /programmes/<code>/"""
        serializer = ProgrammeUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = ProgrammeDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a programme",
        responses={
            204: OpenApiResponse(description="Programme deleted successfully."),
            404: OpenApiResponse(description="Programme not found."),
            422: OpenApiResponse(description="Protected programmes cannot be deleted."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /programmes/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a programme",
        responses={
            200: ProgrammeDetailSerializer,
            404: OpenApiResponse(description="Programme not found."),
            422: OpenApiResponse(
                description="Protected programmes cannot be modified."
            ),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /programmes/<code>/activate/"""
        obj = self.service.activate(code=code)
        data = ProgrammeDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a programme",
        responses={
            200: ProgrammeDetailSerializer,
            404: OpenApiResponse(description="Programme not found."),
            422: OpenApiResponse(
                description="Protected programmes cannot be modified."
            ),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /programmes/<code>/deactivate/"""
        obj = self.service.deactivate(code=code)
        data = ProgrammeDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )
