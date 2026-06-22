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
    UpdatePreferencesSerializer,
    UpdateProfileSerializer,
    UserAdminCreateSerializer,
    UserAdminDetailSerializer,
    UserAdminListSerializer,
    UserMeSerializer,
)
from apps.users.services import (
    UserAvatarService,
    UserPreferencesService,
    UserProfileService,
    UsersAdminService,
    UsersExportService,
)

logger = logging.getLogger(__name__)

_ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_MAX_AVATAR_SIZE_MB = 5


@extend_schema(tags=["Users"])
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
        summary="Search users",
        description=(
            "Returns active users matching the given query (display name or email). "
            "Intended for typeahead / mention search."
        ),
        responses={
            200: OpenApiResponse(description="Results returned."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(detail=False, methods=["get"], url_path="search", url_name="search")
    def search(self, request: Request):
        """GET /users/search/?q=<query>"""
        from django.db.models import Q

        from apps.users.models import User

        q = request.query_params.get("q", "").strip()
        qs = User.objects.filter(is_active=True).select_related("profile")
        if q:
            qs = qs.filter(
                Q(profile__display_name__icontains=q) | Q(email__icontains=q)
            )
        qs = qs.order_by("profile__display_name")[:20]
        results = [
            {
                "code": getattr(u.profile, "code", None),
                "display_name": getattr(u.profile, "display_name", u.email),
                "email": u.email,
            }
            for u in qs
            if hasattr(u, "profile")
        ]
        return self.response(data={"results": results})

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


@extend_schema(tags=["Users"])
class UsersAdminViewSet(ExportMixin, BaseViewSet):
    """Admin-facing endpoints for managing system users."""

    export_service_class = UsersExportService
    export_columns = [
        {"key": "display_name", "label": "Display Name", "default": True},
        {"key": "first_name", "label": "First Name", "default": True},
        {"key": "last_name", "label": "Last Name", "default": True},
        {"key": "email", "label": "Email", "default": True},
        {"key": "auth_type", "label": "Auth Type", "default": True},
        {"key": "last_login", "label": "Last Login", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": False},
        {"key": "created_by", "label": "Created By", "default": False},
    ]

    def _users_service(self) -> UsersAdminService:
        return UsersAdminService(user=self.request.user, request=self.request)

    def get_permissions(self):
        from apps.core.permissions import HasPermission

        if self.action in ("list", "retrieve", "stats"):
            return [HasPermission("auth.view_user")]
        if self.action in ("export_specs", "export"):
            return [HasPermission("auth.view_user")]
        if self.action == "create":
            return [HasPermission("auth.add_user")]
        if self.action == "destroy":
            return [HasPermission("auth.delete_user")]
        if self.action in ("activate", "deactivate", "reset_password"):
            return [HasPermission("auth.change_user")]
        return [HasPermission("auth.view_user")]

    @extend_schema(
        summary="List users",
        description="Returns a paginated list of all users.",
        responses={
            200: OpenApiResponse(description="Users returned."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def list(self, request: Request):
        """GET /users/"""
        params = self.get_list_params(request)
        result = self._users_service().list(params=params)
        return self.paginated_response(
            result=result,
            serializer_class=UserAdminListSerializer,
        )

    @extend_schema(
        summary="Get user",
        description="Returns a single user by profile code.",
        responses={
            200: OpenApiResponse(description="User returned."),
            404: OpenApiResponse(description="Not found."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def retrieve(self, request: Request, code: str = ""):
        """GET /users/<code>/"""
        obj = self._users_service().get(code=code)
        serializer = UserAdminDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create user",
        description=(
            "Creates a new classic-auth user and sends a password setup email. "
            "Only available when AUTH_MODE=classic."
        ),
        request=UserAdminCreateSerializer,
        responses={
            201: OpenApiResponse(description="User created."),
            400: OpenApiResponse(description="Validation error."),
            409: OpenApiResponse(description="Email already registered."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def create(self, request: Request):
        """POST /users/"""
        serializer = UserAdminCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self._users_service().create(**serializer.validated_data)
        response_serializer = UserAdminListSerializer(
            obj, context=self.get_serializer_context()
        )
        from rest_framework import status as drf_status

        return self.response(
            data=response_serializer.data,
            message="User created. A setup email has been sent.",
            status_code=drf_status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Delete user",
        description="Permanently deletes a user and all associated data.",
        responses={
            204: OpenApiResponse(description="User deleted."),
            404: OpenApiResponse(description="Not found."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    def destroy(self, request: Request, code: str = ""):
        """DELETE /users/<code>/"""
        from rest_framework import status as drf_status

        self._users_service().delete(code=code)
        return self.response(
            message="User deleted.", status_code=drf_status.HTTP_204_NO_CONTENT
        )

    @extend_schema(
        summary="User stats",
        description="Returns aggregate counts for users.",
        responses={
            200: OpenApiResponse(description="Stats returned."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(detail=False, methods=["get"], url_path="stats", url_name="stats")
    def stats(self, request: Request):
        """GET /users/stats/"""
        data = self._users_service().stats()
        return self.response(data=data)

    @extend_schema(
        summary="Activate user",
        description="Activates a deactivated user account.",
        responses={
            200: OpenApiResponse(description="User activated."),
            404: OpenApiResponse(description="Not found."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="<str:code>/activate",
        url_name="activate",
    )
    def activate(self, request: Request, code: str = ""):
        """POST /users/<code>/activate/"""
        obj = self._users_service().activate(code=code)
        serializer = UserAdminListSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data, message="User activated.")

    @extend_schema(
        summary="Deactivate user",
        description="Deactivates an active user account.",
        responses={
            200: OpenApiResponse(description="User deactivated."),
            404: OpenApiResponse(description="Not found."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="<str:code>/deactivate",
        url_name="deactivate",
    )
    def deactivate(self, request: Request, code: str = ""):
        """POST /users/<code>/deactivate/"""
        obj = self._users_service().deactivate(code=code)
        serializer = UserAdminListSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data, message="User deactivated.")

    @extend_schema(
        summary="Admin password reset",
        description=(
            "Sends a password reset link to the user's email. "
            "Only available for classic auth users."
        ),
        responses={
            200: OpenApiResponse(description="Reset link sent."),
            404: OpenApiResponse(description="Not found."),
            422: OpenApiResponse(description="Not a classic auth user."),
            401: OpenApiResponse(description="Authentication required."),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="<str:code>/reset-password",
        url_name="reset-password",
    )
    def reset_password(self, request: Request, code: str = ""):
        """POST /users/<code>/reset-password/"""
        self._users_service().send_admin_password_reset(code=code)
        return self.response(message="Password reset link sent.")
