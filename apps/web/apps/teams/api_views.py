from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.teams.serializers import (
    TeamCreateSerializer,
    TeamDetailSerializer,
    TeamListSerializer,
    TeamUpdateSerializer,
)
from apps.teams.services import TeamExportService, TeamImportService, TeamService
from apps.users.serializers import MemberMiniListSerializer
from apps.users.services import MembersService


@extend_schema(tags=["Teams"])
class TeamViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = TeamService
    import_service_class = TeamImportService
    export_service_class = TeamExportService

    # Import metadata surfaced via GET /teams/import/specs
    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "Team name (max 120 chars).",
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
        "Rows with duplicate names are skipped and reported in errors.",
        f"Maximum {TeamImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {TeamImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "teams_import_template.csv"

    # Export column specs surfaced via GET /teams/export/specs/
    export_columns = [
        {"key": "name", "label": "Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "description", "label": "Description", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Engineering", "Core engineering team", "true"]

    def get_permissions(self):
        action_perms = {
            "list": "teams.view_team",
            "retrieve": "teams.view_team",
            "members": "teams.view_team",
            "create": "teams.add_team",
            "partial_update": "teams.change_team",
            "destroy": "teams.delete_team",
            "activate": "teams.change_team",
            "deactivate": "teams.change_team",
            "statistics": "teams.view_team",
            "options": "teams.view_team",
            "import_specs": "teams.import_team",
            "import_sample": "teams.import_team",
            "import_bulk": "teams.import_team",
            "export_specs": "teams.export_team",
            "export": "teams.export_team",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return TeamListSerializer

    def get_retrieve_serializer_class(self):
        return TeamDetailSerializer

    def get_create_serializer_class(self):
        return TeamCreateSerializer

    def get_update_serializer_class(self):
        return TeamUpdateSerializer

    def get_create_response_serializer_class(self):
        return TeamDetailSerializer

    @extend_schema(
        summary="List team options",
        description=(
            "Returns a lightweight list of active teams (code + name) for use in "
            "picker fields."
        ),
        responses={200: OpenApiResponse(description="List of active team options.")},
    )
    def options(self, request: Request):
        """GET /teams/options/"""
        return self.response(
            data=self.service.options(),
            message="Team options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List teams",
        description=(
            "Returns a paginated list of teams. "
            "Defaults to active teams only. Pass `is_active=false` to list "
            "inactive teams. Supports `search` by name and `ordering`."
        ),
        responses={200: TeamListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /teams/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a team",
        responses={
            200: TeamDetailSerializer,
            404: OpenApiResponse(description="Team not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /teams/<code>/"""
        obj = self.service.get(code=code)
        serializer = TeamDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a team",
        request=TeamCreateSerializer,
        responses={
            201: TeamDetailSerializer,
            409: OpenApiResponse(description="A team with this name already exists."),
        },
    )
    def create(self, request: Request):
        """POST /teams/"""
        return super().create(request)

    @extend_schema(
        summary="Update a team",
        request=TeamUpdateSerializer,
        responses={
            200: TeamDetailSerializer,
            404: OpenApiResponse(description="Team not found."),
            409: OpenApiResponse(description="A team with this name already exists."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /teams/<code>/"""
        serializer = TeamUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        team = self.service.update(code=code, **serializer.validated_data)
        data = TeamDetailSerializer(team, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a team",
        responses={
            204: OpenApiResponse(description="Team deleted successfully."),
            404: OpenApiResponse(description="Team not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /teams/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a team",
        responses={
            200: TeamDetailSerializer,
            404: OpenApiResponse(description="Team not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /teams/<code>/activate/"""
        team = self.service.activate(code=code)
        data = TeamDetailSerializer(team, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a team",
        responses={
            200: TeamDetailSerializer,
            404: OpenApiResponse(description="Team not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /teams/<code>/deactivate/"""
        team = self.service.deactivate(code=code)
        data = TeamDetailSerializer(team, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )

    @extend_schema(
        summary="List team members",
        description="Returns a paginated list of members assigned to the team.",
        responses={
            200: MemberMiniListSerializer(many=True),
            404: OpenApiResponse(description="Team not found."),
        },
    )
    def members(self, request: Request, code=None):
        """GET /teams/<code>/members/"""
        self.service.get(code=code)
        svc = MembersService(user=request.user, request=request)
        params = self.get_list_params(request)
        params.filters["team"] = code
        result = svc.list(params=params)
        return self.paginated_response(
            result=result,
            serializer_class=MemberMiniListSerializer,
        )
