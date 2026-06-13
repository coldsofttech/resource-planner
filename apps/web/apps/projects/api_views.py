from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.exceptions import NotFoundException
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.projects import selectors as project_selectors
from apps.projects.serializers import (
    ProgrammeCreateSerializer,
    ProgrammeDetailSerializer,
    ProgrammeListSerializer,
    ProgrammeUpdateSerializer,
    ProjectStatusDetailSerializer,
    ProjectStatusListSerializer,
    ProjectSubStatusCreateSerializer,
    ProjectSubStatusDetailSerializer,
    ProjectSubStatusListSerializer,
    ProjectSubStatusReorderSerializer,
    ProjectSubStatusUpdateSerializer,
    ProjectTypeCreateSerializer,
    ProjectTypeDetailSerializer,
    ProjectTypeListSerializer,
    ProjectTypeUpdateSerializer,
)
from apps.projects.services import (
    ProgrammeExportService,
    ProgrammeImportService,
    ProgrammeService,
    ProjectStatusExportService,
    ProjectStatusService,
    ProjectSubStatusExportService,
    ProjectSubStatusGlobalImportService,
    ProjectSubStatusImportService,
    ProjectSubStatusService,
    ProjectTypeExportService,
    ProjectTypeImportService,
    ProjectTypeService,
)


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


class ProjectStatusViewSet(ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = ProjectStatusService
    export_service_class = ProjectStatusExportService

    export_columns = [
        {"key": "name", "label": "Project Status Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectstatus",
            "retrieve": "projects.view_projectstatus",
            "options": "projects.view_projectstatus",
            "statistics": "projects.view_projectstatus",
            "export_specs": "projects.export_projectstatus",
            "export": "projects.export_projectstatus",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return ProjectStatusListSerializer

    def get_retrieve_serializer_class(self):
        return ProjectStatusDetailSerializer

    @extend_schema(
        summary="List project status options",
        responses={
            200: OpenApiResponse(description="List of active project status options.")
        },
    )
    def options(self, request: Request):
        """GET /projects/statuses/options/"""
        return self.response(
            data=self.service.options(),
            message="Project status options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List project statuses",
        responses={200: ProjectStatusListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /projects/statuses/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a project status",
        responses={
            200: ProjectStatusDetailSerializer,
            404: OpenApiResponse(description="Project status not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /projects/statuses/<code>/"""
        obj = self.service.get(code=code)
        serializer = ProjectStatusDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)


class ProjectSubStatusViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = ProjectSubStatusService
    import_service_class = ProjectSubStatusImportService
    export_service_class = ProjectSubStatusExportService

    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": (
                "Sub-status name (max 100 chars, must be unique within the "
                "parent status)."
            ),
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
        "Rows with duplicate sub-status names within the parent status are skipped.",
        f"Maximum {ProjectSubStatusImportService.MAX_IMPORT_ROWS} data rows per file.",
        (
            f"Maximum file size: "
            f"{ProjectSubStatusImportService.MAX_IMPORT_FILE_SIZE_MB} MB."
        ),
    ]
    import_sample_filename = "project_sub_statuses_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Sub-Status Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "main_status", "label": "Main Status", "default": True},
        {"key": "order", "label": "Order", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Draft", "true"]

    def _get_parent_status(self):
        status_code = self.kwargs.get("status_code")
        parent = project_selectors.get_project_status_by_code(status_code)
        if parent is None:
            raise NotFoundException(
                resource="ProjectStatus", lookup_field="code", lookup_value=status_code
            )
        return parent

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectsubstatus",
            "retrieve": "projects.view_projectsubstatus",
            "options": "projects.view_projectsubstatus",
            "statistics": "projects.view_projectsubstatus",
            "create": "projects.add_projectsubstatus",
            "partial_update": "projects.change_projectsubstatus",
            "destroy": "projects.delete_projectsubstatus",
            "activate": "projects.change_projectsubstatus",
            "deactivate": "projects.change_projectsubstatus",
            "reorder": "projects.change_projectsubstatus",
            "import_specs": "projects.import_projectsubstatus",
            "import_sample": "projects.import_projectsubstatus",
            "import_bulk": "projects.import_projectsubstatus",
            "export_specs": "projects.export_projectsubstatus",
            "export": "projects.export_projectsubstatus",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return ProjectSubStatusListSerializer

    def get_retrieve_serializer_class(self):
        return ProjectSubStatusDetailSerializer

    def get_create_serializer_class(self):
        return ProjectSubStatusCreateSerializer

    def get_update_serializer_class(self):
        return ProjectSubStatusUpdateSerializer

    def get_create_response_serializer_class(self):
        return ProjectSubStatusDetailSerializer

    @extend_schema(summary="List project sub-statuses for a status")
    def list(self, request: Request, status_code=None):
        """GET /projects/statuses/<status_code>/substatus/"""
        self.service._status_scope = status_code
        return super().list(request)

    @extend_schema(summary="Retrieve a project sub-status")
    def retrieve(self, request: Request, status_code=None, code=None):
        """GET /projects/statuses/<status_code>/substatus/<code>/"""
        obj = self.service.get(code=code)
        serializer = ProjectSubStatusDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(summary="Create a project sub-status")
    def create(self, request: Request, status_code=None):
        """POST /projects/statuses/<status_code>/substatus/"""
        parent = self._get_parent_status()
        serializer = ProjectSubStatusCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(status=parent, **serializer.validated_data)
        data = ProjectSubStatusDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_create_custom_message(),
            status_code=self.get_create_status_code(),
        )

    @extend_schema(summary="Update a project sub-status")
    def partial_update(self, request: Request, status_code=None, code=None):
        """PATCH /projects/statuses/<status_code>/substatus/<code>/"""
        serializer = ProjectSubStatusUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = ProjectSubStatusDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(summary="Delete a project sub-status")
    def destroy(self, request: Request, status_code=None, code=None):
        """DELETE /projects/statuses/<status_code>/substatus/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(summary="Activate a project sub-status")
    def activate(self, request: Request, status_code=None, code=None):
        """POST /projects/statuses/<status_code>/substatus/<code>/activate/"""
        obj = self.service.activate(code=code)
        data = ProjectSubStatusDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(summary="Deactivate a project sub-status")
    def deactivate(self, request: Request, status_code=None, code=None):
        """POST /projects/statuses/<status_code>/substatus/<code>/deactivate/"""
        obj = self.service.deactivate(code=code)
        data = ProjectSubStatusDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )

    @extend_schema(summary="List sub-status options for a status")
    def options(self, request: Request, status_code=None):
        """GET /projects/statuses/<status_code>/substatus/options/"""
        return self.response(
            data=self.service.options(status_code=status_code),
            message="Project sub-status options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(summary="Sub-status statistics for a status")
    def statistics(self, request: Request, status_code=None):
        """GET /projects/statuses/<status_code>/substatus/stats/"""
        fields = request.query_params.getlist("fields")
        data = self.service.stats(fields=fields or None, status_code=status_code)
        return self.response(
            data=data,
            message="Project sub-status statistics retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(summary="Reorder sub-statuses for a status")
    def reorder(self, request: Request, status_code=None):
        """POST /projects/statuses/<status_code>/substatus/reorder/"""
        parent = self._get_parent_status()
        serializer = ProjectSubStatusReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.service.reorder(status=parent, codes=serializer.validated_data["codes"])
        return self.response(
            message="Sub-statuses reordered successfully.",
            status_code=status.HTTP_200_OK,
        )

    def import_specs(self, request: Request, status_code=None):
        """GET /projects/statuses/<status_code>/substatus/import/specs/"""
        return super().import_specs(request)

    def import_sample(self, request: Request, status_code=None):
        """GET /projects/statuses/<status_code>/substatus/import/sample/"""
        return super().import_sample(request)

    def export_specs(self, request: Request, status_code=None):
        """GET /projects/statuses/<status_code>/substatus/export/specs/"""
        return super().export_specs(request)

    def import_bulk(self, request: Request, status_code=None):
        """POST /projects/statuses/<status_code>/substatus/import/"""
        parent = self._get_parent_status()
        file = request.FILES.get("file")
        if not file:
            from apps.core.exceptions import ValidationException

            raise ValidationException("No file provided.")
        dry_run = request.data.get("dry_run", "false").lower() in ("true", "1")
        result = self.import_service.bulk_import(file, dry_run=dry_run, status=parent)
        return self.response(
            data=result,
            message="Import completed.",
            status_code=status.HTTP_200_OK,
        )

    def export(self, request: Request, status_code=None):
        """GET /projects/statuses/<status_code>/substatus/export/"""
        parent = self._get_parent_status()
        fields = request.query_params.getlist("fields") or None
        export_format = request.query_params.get("format", "csv")
        filters = {
            k: v
            for k, v in request.query_params.items()
            if k not in ("fields", "format")
        }
        return self.export_service.export(
            fields=fields,
            export_format=export_format,
            filters=filters or None,
            status=parent,
        )


class ProjectSubStatusFlatOptionsViewSet(BaseViewSet):
    """Flat options endpoint — all active sub-statuses across all statuses."""

    service_class = ProjectSubStatusService

    def get_permissions(self):
        return [IsAuthenticated(), HasPermission("projects.view_projectsubstatus")]

    @extend_schema(summary="List all active project sub-status options")
    def options(self, request: Request):
        """GET /projects/sub-statuses/options/"""
        return self.response(
            data=self.service.options(status_code=None),
            message="Project sub-status options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class ProjectSubStatusGlobalViewSet(ImportMixin, ExportMixin, BaseViewSet):
    """Global sub-status import/export — no parent status required in URL."""

    service_class = ProjectSubStatusService
    import_service_class = ProjectSubStatusGlobalImportService
    export_service_class = ProjectSubStatusExportService

    import_fields = [
        {
            "name": "main_status_code",
            "type": "string",
            "required": True,
            "description": "Code of the parent project status (e.g. PROJSTAT-1).",
        },
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": (
                "Sub-status name (max 100 chars, must be unique within parent)."
            ),
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
        "Both 'main_status_code' and 'name' columns are required.",
        "Rows with duplicate sub-status names within the parent status are skipped.",
        (
            f"Maximum {ProjectSubStatusGlobalImportService.MAX_IMPORT_ROWS} "
            f"data rows per file."
        ),
        (
            f"Maximum file size: "
            f"{ProjectSubStatusGlobalImportService.MAX_IMPORT_FILE_SIZE_MB} MB."
        ),
    ]
    import_sample_filename = "project_sub_statuses_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Sub-Status Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "main_status", "label": "Main Status", "default": True},
        {"key": "order", "label": "Order", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["PROJSTAT-1", "Draft", "true"]

    def get_permissions(self):
        action_perms = {
            "import_specs": "projects.import_projectsubstatus",
            "import_sample": "projects.import_projectsubstatus",
            "import_bulk": "projects.import_projectsubstatus",
            "export_specs": "projects.export_projectsubstatus",
            "export": "projects.export_projectsubstatus",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return super().get_permissions()
