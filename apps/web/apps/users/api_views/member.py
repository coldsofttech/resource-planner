import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request

from apps.core.viewsets import BaseViewSet, ExportMixin
from apps.users.serializers import (
    AssignMemberSerializer,
    MemberListSerializer,
    MemberUpdateSerializer,
)
from apps.users.services import MembersExportService, MembersService

logger = logging.getLogger(__name__)


@extend_schema(tags=["Members"])
class MembersViewSet(ExportMixin, BaseViewSet):
    """Admin-facing endpoints for viewing and updating member workforce details."""

    export_service_class = MembersExportService
    export_columns = [
        {"key": "code", "label": "Code", "default": True},
        {"key": "first_name", "label": "First Name", "default": True},
        {"key": "last_name", "label": "Last Name", "default": True},
        {"key": "display_name", "label": "Display Name", "default": True},
        {"key": "email", "label": "Email", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "location", "label": "Location", "default": True},
        {"key": "employment_type", "label": "Employment Type", "default": True},
        {"key": "role", "label": "Role", "default": True},
        {"key": "joined_date", "label": "Joined Date", "default": True},
        {"key": "leaving_date", "label": "Leaving Date", "default": False},
        {"key": "default_holidays", "label": "Default Holidays", "default": False},
        {"key": "created_at", "label": "Created On", "default": False},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def _members_service(self) -> MembersService:
        return MembersService(user=self.request.user, request=self.request)

    def get_permissions(self):
        from apps.core.permissions import HasPermission

        if self.action in ("list", "retrieve"):
            return [HasPermission("users.view_user")]
        if self.action in ("export_specs", "export"):
            return [HasPermission("users.export_member")]
        if self.action == "assign_team":
            return [HasPermission("teams.assign_team")]
        return [HasPermission("users.change_user_workforce")]

    @extend_schema(
        summary="List members",
        description="Returns a paginated list of all active members.",
        responses={
            200: OpenApiResponse(description="Members returned."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def list(self, request: Request):
        """GET /members/"""
        params = self.get_list_params(request)
        result = self._members_service().list(params=params)
        return self.paginated_response(
            result=result,
            serializer_class=MemberListSerializer,
        )

    @extend_schema(
        summary="Get member",
        description="Returns a single member by profile code.",
        responses={
            200: OpenApiResponse(description="Member returned."),
            404: OpenApiResponse(description="Not found."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def retrieve(self, request: Request, code: str = ""):
        """GET /members/<code>/"""
        obj = self._members_service().get(code=code)
        serializer = MemberListSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Update member",
        description="Updates workforce details for a member.",
        request=MemberUpdateSerializer,
        responses={
            200: OpenApiResponse(description="Member updated."),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def partial_update(self, request: Request, code: str = ""):
        """PATCH /members/<code>/"""
        serializer = MemberUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self._members_service().update(code=code, **serializer.validated_data)
        response_serializer = MemberListSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=response_serializer.data, message="Member updated.")

    @extend_schema(
        summary="Member options",
        description="Returns configuration options for the members module.",
        responses={
            200: OpenApiResponse(description="Options returned."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(detail=False, methods=["get"], url_path="options", url_name="options")
    def options(self, request: Request):
        """GET /members/options/"""
        from apps.configurations.selectors import Holidays

        try:
            default_holidays = Holidays.get_default_holidays()
        except Exception:
            default_holidays = None
        return self.response(data={"default_holidays": default_holidays})

    @extend_schema(
        summary="Assign member to team(s)",
        description=(
            "Assigns a member to one or more teams. "
            "Non-leadership members may only be assigned to one team at a time. "
            "Pass an empty teams list to unassign from all teams "
            "(requires unassign_team permission)."
        ),
        request=AssignMemberSerializer,
        responses={
            200: OpenApiResponse(description="Assignment updated."),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication required."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Member or team not found."),
        },
    )
    def assign_team(self, request: Request, code: str = ""):
        """POST /members/<code>/assign-team/"""
        from apps.core.exceptions import PermissionException
        from apps.teams.services import AssignmentService

        serializer = AssignMemberSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        teams = serializer.validated_data["teams"]

        # Unassigning (empty teams) requires the separate unassign_team permission.
        if not teams and not request.user.has_perm("teams.unassign_team"):
            raise PermissionException()

        AssignmentService(user=request.user).assign(
            member_code=code,
            teams=teams,
            note=serializer.validated_data.get("note", ""),
        )
        obj = self._members_service().get(code=code)
        response_serializer = MemberListSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(
            data=response_serializer.data, message="Team assignment updated."
        )
