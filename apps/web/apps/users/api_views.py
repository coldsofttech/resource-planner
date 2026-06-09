import logging

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request

from apps.core.exceptions import ValidationException
from apps.core.viewsets import BaseViewSet, ExportMixin
from apps.users.serializers import (
    ChangePasswordSerializer,
    MemberListSerializer,
    MemberUpdateSerializer,
    UpdatePreferencesSerializer,
    UpdateProfileSerializer,
    UserMeSerializer,
)
from apps.users.services import (
    MembersExportService,
    MembersService,
    UserAvatarService,
    UserPreferencesService,
    UserProfileService,
)

logger = logging.getLogger(__name__)

_ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_MAX_AVATAR_SIZE_MB = 5


class UserMeViewSet(BaseViewSet):
    """Endpoints for the authenticated user's own account."""

    def _preferences_service(self) -> UserPreferencesService:
        return UserPreferencesService(user=self.request.user, request=self.request)

    def _profile_service(self) -> UserProfileService:
        return UserProfileService(user=self.request.user, request=self.request)

    def _avatar_service(self) -> UserAvatarService:
        return UserAvatarService(user=self.request.user, request=self.request)

    @extend_schema(
        summary="Get full profile",
        description="Returns the authenticated user's complete profile.",
        responses={
            200: OpenApiResponse(description="Profile returned."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(detail=False, methods=["get"], url_path="me", url_name="me-get")
    def me(self, request: Request):
        """GET /users/me/"""
        data = self._profile_service().get_me()
        serializer = UserMeSerializer(data)
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Update UI preferences",
        description="Updates the authenticated user's UI preferences (e.g. theme).",
        request=UpdatePreferencesSerializer,
        responses={
            200: OpenApiResponse(description="Preferences updated."),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(
        detail=False,
        methods=["patch"],
        url_path="me/preferences",
        url_name="me-preferences",
    )
    def update_preferences(self, request: Request):
        """PATCH /users/me/preferences/"""
        serializer = UpdatePreferencesSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self._preferences_service().update_theme(
            theme=serializer.validated_data["theme"],
        )
        return self.response(message="Preferences updated.")

    @extend_schema(
        summary="Update profile",
        description=(
            "Updates the authenticated user's profile fields: "
            "first_name, last_name, display_name, timezone, skills."
        ),
        request=UpdateProfileSerializer,
        responses={
            200: OpenApiResponse(description="Profile updated."),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(
        detail=False, methods=["patch"], url_path="me/profile", url_name="me-profile"
    )
    def update_profile(self, request: Request):
        """PATCH /users/me/profile/"""
        serializer = UpdateProfileSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self._profile_service().update_profile(**serializer.validated_data)
        return self.response(message="Profile updated.")

    @extend_schema(
        summary="Change password",
        description="Changes the authenticated user's password. Classic auth only.",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password changed."),
            400: OpenApiResponse(
                description="Validation error or incorrect current password."
            ),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(
        detail=False, methods=["post"], url_path="me/password", url_name="me-password"
    )
    def change_password(self, request: Request):
        """POST /users/me/password/"""
        from django.contrib.auth import update_session_auth_hash

        serializer = ChangePasswordSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self._profile_service().change_password(
            current_password=serializer.validated_data["current_password"],
            new_password=serializer.validated_data["new_password"],
        )
        update_session_auth_hash(request, request.user)
        return self.response(message="Password updated successfully.")

    @extend_schema(
        summary="Get avatar",
        description="Returns the authenticated user's avatar image.",
        responses={
            200: OpenApiResponse(description="Avatar image."),
            404: OpenApiResponse(description="No avatar set."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(
        detail=False, methods=["get"], url_path="me/avatar", url_name="me-avatar-get"
    )
    def get_avatar(self, request: Request):
        """GET /users/me/avatar/"""
        result = self._profile_service().get_avatar_bytes()
        if result is None:
            return HttpResponse(status=404)
        content, content_type = result
        resp = HttpResponse(content, content_type=content_type)
        resp["Cache-Control"] = "private, max-age=3600"
        return resp

    @extend_schema(
        summary="Upload avatar",
        description="Uploads a new avatar image for the authenticated user.",
        responses={
            200: OpenApiResponse(description="Avatar uploaded."),
            400: OpenApiResponse(description="Invalid file."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="me/avatar/upload",
        url_name="me-avatar-upload",
        parser_classes=[MultiPartParser],
    )
    def upload_avatar(self, request: Request):
        """POST /users/me/avatar/upload/"""
        uploaded_file = request.FILES.get("avatar")
        if not uploaded_file:
            raise ValidationException("No avatar file uploaded.")

        content_type = uploaded_file.content_type or ""
        if content_type not in _ALLOWED_AVATAR_TYPES:
            raise ValidationException(
                "Invalid file type. Allowed: JPEG, PNG, GIF, WEBP."
            )

        max_bytes = _MAX_AVATAR_SIZE_MB * 1024 * 1024
        if uploaded_file.size > max_bytes:
            raise ValidationException(
                f"File too large. Maximum size is {_MAX_AVATAR_SIZE_MB} MB."
            )

        _ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        profile_code = getattr(
            getattr(request.user, "profile", None), "code", None
        ) or str(request.user.pk)
        filename = f"{profile_code}_avatar{_ext_map.get(content_type, '.jpg')}"

        file_data = uploaded_file.read()
        self._avatar_service().upload(
            file_data=file_data,
            filename=filename,
            content_type=content_type,
        )
        return self.response(
            data={"avatar_url": "/api/v1/users/me/avatar/"},
            message="Avatar uploaded successfully.",
        )

    @extend_schema(
        summary="User options",
        description="Returns available timezone options.",
        responses={
            200: OpenApiResponse(description="Options returned."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(detail=False, methods=["get"], url_path="options", url_name="options")
    def options(self, request: Request):
        """GET /users/options/"""
        timezones = UserProfileService.get_timezone_options()
        return self.response(data={"timezones": timezones})

    @extend_schema(
        summary="Get user avatar",
        description="Returns the avatar image for a specific user by primary key.",
        responses={
            200: OpenApiResponse(description="Avatar image."),
            204: OpenApiResponse(description="No avatar set."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="<str:code>/avatar",
        url_name="user-avatar-get",
    )
    def get_user_avatar(self, request: Request, code: str = ""):
        """GET /users/<code>/avatar/ — avatar looked up by profile code."""
        from apps.users.models import UserProfile

        try:
            profile = UserProfile.objects.select_related("user").get(code=code)
        except UserProfile.DoesNotExist:
            return HttpResponse(status=404)

        avatar_service = UserProfileService(user=profile.user, request=request)
        result = avatar_service.get_avatar_bytes()
        if result is None:
            return HttpResponse(status=204)
        content, content_type = result
        resp = HttpResponse(content, content_type=content_type)
        resp["Cache-Control"] = "private, max-age=3600"
        return resp


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
