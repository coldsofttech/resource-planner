import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request

from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin
from apps.users.serializers import (
    GroupAdminListSerializer,
    GroupAssignMemberSerializer,
    GroupCreateSerializer,
    GroupMemberSerializer,
    GroupUpdateSerializer,
)
from apps.users.services import (
    GroupsAdminService,
    GroupsExportService,
    GroupsImportService,
)

logger = logging.getLogger(__name__)


@extend_schema(tags=["Groups"])
class GroupsAdminViewSet(ImportMixin, ExportMixin, BaseViewSet):
    """Admin-facing endpoints for managing groups."""

    import_service_class = GroupsImportService
    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "Group name (max 150 chars).",
        },
        {
            "name": "description",
            "type": "string",
            "required": False,
            "description": "Optional description.",
        },
    ]
    import_notes = [
        "The first row must be a header row.",
        "The 'name' column is required; all other columns are optional.",
        "Rows with duplicate names are skipped and reported in errors.",
        f"Maximum {GroupsImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {GroupsImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "groups_import_template.csv"

    export_service_class = GroupsExportService
    export_columns = [
        {"key": "name", "label": "Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "description", "label": "Description", "default": True},
        {"key": "is_admin_group", "label": "Admin Group", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "member_count", "label": "Member Count", "default": True},
        {"key": "created_at", "label": "Created On", "default": False},
        {"key": "created_by", "label": "Created By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Project Managers", "Manages all project managers"]

    def _groups_service(self) -> GroupsAdminService:
        return GroupsAdminService(user=self.request.user, request=self.request)

    def get_permissions(self):
        from apps.core.permissions import HasPermission

        if self.action in ("list", "retrieve", "stats", "members"):
            return [HasPermission("users.view_group")]
        if self.action in ("export_specs", "export"):
            return [HasPermission("users.export_group")]
        if self.action in ("import_specs", "import_sample", "import_bulk"):
            return [HasPermission("users.import_group")]
        if self.action == "create":
            return [HasPermission("users.add_group")]
        if self.action == "destroy":
            return [HasPermission("users.delete_group")]
        if self.action in (
            "partial_update",
            "activate",
            "deactivate",
            "assign_member",
            "unassign_member",
        ):
            return [HasPermission("users.change_group")]
        return [HasPermission("users.view_group")]

    @extend_schema(
        summary="List groups",
        responses={200: OpenApiResponse(description="Groups returned.")},
    )
    def list(self, request: Request):
        """GET /groups/"""
        params = self.get_list_params(request)
        result = self._groups_service().list(params=params)
        return self.paginated_response(
            result=result, serializer_class=GroupAdminListSerializer
        )

    @extend_schema(
        summary="Get group",
        responses={
            200: OpenApiResponse(description="Group returned."),
            404: OpenApiResponse(description="Not found."),
        },
    )
    def retrieve(self, request: Request, code: str = ""):
        """GET /groups/<code>/"""
        obj = self._groups_service().get(code=code)
        serializer = GroupAdminListSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create group",
        request=GroupCreateSerializer,
        responses={
            201: OpenApiResponse(description="Group created."),
            400: OpenApiResponse(description="Validation error."),
            409: OpenApiResponse(description="Name already in use."),
        },
    )
    def create(self, request: Request):
        """POST /groups/"""
        from rest_framework import status as drf_status

        serializer = GroupCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self._groups_service().create(**serializer.validated_data)
        response_serializer = GroupAdminListSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(
            data=response_serializer.data,
            message="Group created.",
            status_code=drf_status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update group",
        request=GroupUpdateSerializer,
        responses={
            200: OpenApiResponse(description="Group updated."),
            400: OpenApiResponse(description="Validation error."),
            404: OpenApiResponse(description="Not found."),
        },
    )
    def partial_update(self, request: Request, code: str = ""):
        """PATCH /groups/<code>/"""
        serializer = GroupUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self._groups_service().update(code=code, **serializer.validated_data)
        response_serializer = GroupAdminListSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=response_serializer.data, message="Group updated.")

    @extend_schema(
        summary="Delete group",
        responses={
            204: OpenApiResponse(description="Group deleted."),
            404: OpenApiResponse(description="Not found."),
        },
    )
    def destroy(self, request: Request, code: str = ""):
        """DELETE /groups/<code>/"""
        from rest_framework import status as drf_status

        self._groups_service().delete(code=code)
        return self.response(
            message="Group deleted.", status_code=drf_status.HTTP_204_NO_CONTENT
        )

    @extend_schema(
        summary="Group stats",
        responses={200: OpenApiResponse(description="Stats returned.")},
    )
    @action(detail=False, methods=["get"], url_path="stats", url_name="stats")
    def stats(self, request: Request):
        """GET /groups/stats/"""
        data = self._groups_service().stats()
        return self.response(data=data)

    @extend_schema(
        summary="Activate group",
        responses={
            200: OpenApiResponse(description="Group activated."),
            404: OpenApiResponse(description="Not found."),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="<str:code>/activate",
        url_name="activate",
    )
    def activate(self, request: Request, code: str = ""):
        """POST /groups/<code>/activate/"""
        obj = self._groups_service().activate(code=code)
        serializer = GroupAdminListSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data, message="Group activated.")

    @extend_schema(
        summary="Deactivate group",
        responses={
            200: OpenApiResponse(description="Group deactivated."),
            404: OpenApiResponse(description="Not found."),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="<str:code>/deactivate",
        url_name="deactivate",
    )
    def deactivate(self, request: Request, code: str = ""):
        """POST /groups/<code>/deactivate/"""
        obj = self._groups_service().deactivate(code=code)
        serializer = GroupAdminListSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data, message="Group deactivated.")

    @extend_schema(
        summary="List or assign group members",
        responses={200: OpenApiResponse(description="Members returned.")},
    )
    @action(
        detail=False,
        methods=["get", "post"],
        url_path="<str:code>/members",
        url_name="members",
    )
    def members(self, request: Request, code: str = ""):
        """GET/POST /groups/<code>/members/"""
        from rest_framework import status as drf_status

        if request.method == "GET":
            params = self.get_list_params(request)
            result = self._groups_service().list_members(code=code, params=params)
            return self.paginated_response(
                result=result, serializer_class=GroupMemberSerializer
            )

        serializer = GroupAssignMemberSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self._groups_service().assign_member(
            code=code,
            member_code=serializer.validated_data["member_code"],
        )
        return self.response(
            message="Member assigned.", status_code=drf_status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Remove a member from a group",
        responses={
            204: OpenApiResponse(description="Member removed."),
            404: OpenApiResponse(description="Not found."),
        },
    )
    @action(
        detail=False,
        methods=["delete"],
        url_path="<str:code>/members/<str:member_code>",
        url_name="members-unassign",
    )
    def unassign_member(self, request: Request, code: str = "", member_code: str = ""):
        """DELETE /groups/<code>/members/<member_code>/"""
        from rest_framework import status as drf_status

        self._groups_service().unassign_member(code=code, member_code=member_code)
        return self.response(
            message="Member removed.", status_code=drf_status.HTTP_204_NO_CONTENT
        )
