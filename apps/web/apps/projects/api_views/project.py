from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.projects.serializers import (
    ProjectCollaboratorListSerializer,
    ProjectCollaboratorSerializer,
    ProjectCreateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectUpdateSerializer,
)
from apps.projects.services import (
    ProjectExportService,
    ProjectImportService,
    ProjectService,
)


@extend_schema(tags=["Projects"])
class ProjectViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = ProjectService
    import_service_class = ProjectImportService
    export_service_class = ProjectExportService

    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "Project name (max 255 chars, must be unique).",
        },
        {
            "name": "project_type_code",
            "type": "string",
            "required": True,
            "description": "Code of the project type (e.g. PROJTYPE-1).",
        },
        {
            "name": "status_code",
            "type": "string",
            "required": True,
            "description": "Code of the project status (e.g. PROJSTAT-1).",
        },
        {
            "name": "programme_code",
            "type": "string",
            "required": False,
            "description": "Code of the programme. Defaults to 'Others' if omitted.",
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
            "description": "true/false/yes/no/1/0 â€” defaults to true.",
        },
    ]
    import_notes = [
        "The first row must be a header row.",
        "The 'name', 'project_type_code', and 'status_code' columns are required.",
        "Rows with duplicate project names are skipped and reported in errors.",
        f"Maximum {ProjectImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {ProjectImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "projects_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Project Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "display_name", "label": "Display Name", "default": True},
        {"key": "project_type", "label": "Project Type", "default": True},
        {"key": "programme", "label": "Programme", "default": True},
        {"key": "status", "label": "Status", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "description", "label": "Description", "default": False},
        {"key": "sub_status", "label": "Sub Status", "default": False},
        {"key": "assigned_team", "label": "Assigned Team", "default": False},
        {"key": "confidence", "label": "Confidence", "default": False},
        {"key": "priority", "label": "Priority", "default": False},
        {"key": "start_date", "label": "Start Date", "default": False},
        {"key": "end_date", "label": "End Date", "default": False},
        {"key": "commitment_date", "label": "Commitment Date", "default": False},
        {"key": "efforts_issued", "label": "Efforts/Issues", "default": False},
        {"key": "run_cost_applies", "label": "Run Cost Applies", "default": False},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return [
            "My Project",
            "PROJTYPE-1",
            "PROJSTAT-1",
            "PROG-1",
            "Sample project",
            "true",
        ]

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_project",
            "retrieve": "projects.view_project",
            "options": "projects.view_project",
            "statistics": "projects.view_project",
            "create": "projects.add_project",
            "partial_update": "projects.change_project",
            "destroy": "projects.delete_project",
            "activate": "projects.change_project",
            "deactivate": "projects.change_project",
            "collaborators": "projects.view_project",
            "remove_collaborator": "projects.change_project",
            "import_specs": "projects.import_project",
            "import_sample": "projects.import_project",
            "import_bulk": "projects.import_project",
            "export_specs": "projects.export_project",
            "export": "projects.export_project",
        }
        # POST to collaborators requires change permission
        if self.action == "collaborators" and self.request.method == "POST":
            return [IsAuthenticated(), HasPermission("projects.change_project")]
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return ProjectListSerializer

    def get_retrieve_serializer_class(self):
        return ProjectDetailSerializer

    def get_create_serializer_class(self):
        return ProjectCreateSerializer

    def get_update_serializer_class(self):
        return ProjectUpdateSerializer

    def get_create_response_serializer_class(self):
        return ProjectDetailSerializer

    @extend_schema(
        summary="List project options",
        responses={200: OpenApiResponse(description="List of active project options.")},
    )
    def options(self, request: Request):
        """GET /projects/options/
        Supports ?fields=confidence or ?fields=priority for choice options.
        """
        fields = request.query_params.get("fields") or None
        if fields == "confidence":
            return self.response(
                data=self.service.confidence_options(),
                message="Confidence options retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )
        if fields == "priority":
            return self.response(
                data=self.service.priority_options(),
                message="Priority options retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )
        programme_code = request.query_params.get("programme") or None
        return self.response(
            data=self.service.options(programme_code=programme_code),
            message="Project options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List projects",
        responses={200: ProjectListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /projects/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a project",
        responses={
            200: ProjectDetailSerializer,
            404: OpenApiResponse(description="Project not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /projects/<code>/"""
        obj = self.service.get(code=code)
        serializer = ProjectDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a project",
        request=ProjectCreateSerializer,
        responses={
            201: ProjectDetailSerializer,
            409: OpenApiResponse(
                description="A project with this name already exists."
            ),
        },
    )
    def create(self, request: Request):
        """POST /projects/"""
        return super().create(request)

    @extend_schema(
        summary="Update a project",
        request=ProjectUpdateSerializer,
        responses={
            200: ProjectDetailSerializer,
            404: OpenApiResponse(description="Project not found."),
            409: OpenApiResponse(
                description="A project with this name already exists."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /projects/<code>/"""
        serializer = ProjectUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = ProjectDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a project",
        responses={
            204: OpenApiResponse(description="Project deleted successfully."),
            404: OpenApiResponse(description="Project not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /projects/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a project",
        responses={
            200: ProjectDetailSerializer,
            404: OpenApiResponse(description="Project not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /projects/<code>/activate/"""
        obj = self.service.activate(code=code)
        data = ProjectDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a project",
        responses={
            200: ProjectDetailSerializer,
            404: OpenApiResponse(description="Project not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /projects/<code>/deactivate/"""
        obj = self.service.deactivate(code=code)
        data = ProjectDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )

    @extend_schema(
        summary="List or add collaborators for a project",
        responses={
            200: ProjectCollaboratorListSerializer(many=True),
            201: ProjectCollaboratorListSerializer,
            404: OpenApiResponse(description="Project not found."),
            409: OpenApiResponse(description="Team is already a collaborator."),
        },
    )
    def collaborators(self, request: Request, code=None):
        """GET /projects/<code>/collaborators/ â€” list collaborators.
        POST /projects/<code>/collaborators/ â€” add a collaborator.
        """
        if request.method == "GET":
            obj = self.service.get(code=code)
            data = ProjectCollaboratorListSerializer(
                obj.collaborators.all(), many=True
            ).data
            return self.response(
                data=data,
                message="Collaborators retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )

        # POST
        serializer = ProjectCollaboratorSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        collaborator = self.service.add_collaborator(
            project_code=code,
            team_code=serializer.validated_data["team_code"],
        )
        data = ProjectCollaboratorListSerializer(collaborator).data
        return self.response(
            data=data,
            message="Collaborator added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Remove a collaborator from a project",
        responses={
            204: OpenApiResponse(description="Collaborator removed successfully."),
            404: OpenApiResponse(description="Project or collaborator not found."),
        },
    )
    def remove_collaborator(self, request: Request, code=None, team_code=None):
        """DELETE /projects/<code>/collaborators/<team_code>/"""
        self.service.remove_collaborator(project_code=code, team_code=team_code)
        return self.response(
            message="Collaborator removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
