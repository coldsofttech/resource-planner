import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from apps.auth.serializers import (
    ForgotPasswordRequestSerializer,
    ForgotPasswordResetSerializer,
    ForgotPasswordVerifySerializer,
    LoginSerializer,
    RegisterSerializer,
)
from apps.auth.services import AuthService, ForgotPasswordService, RegisterService
from apps.core.exceptions import ValidationException
from apps.core.viewsets import BaseViewSet

logger = logging.getLogger(__name__)


class AuthViewSet(BaseViewSet):
    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    def _auth_service(self):
        return AuthService(user=self.request.user, request=self.request)

    @extend_schema(
        summary="Classic login",
        description=(
            "Authenticates a user with email and password. "
            "Always available for superusers; for other users, requires "
            "AUTH_MODE=classic. On success, establishes a session and returns a "
            "redirect path."
        ),
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful. Session cookie set."),
            400: OpenApiResponse(
                description="Validation error — email or password missing or malformed."
            ),
            401: OpenApiResponse(description="Invalid email or password."),
            403: OpenApiResponse(
                description="Account deactivated, or classic login not enabled."
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="login", url_name="login")
    def login(self, request: Request):
        """POST /auth/login/"""
        serializer = LoginSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        self._auth_service().classic_login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        return self.response(
            data={"redirect": "/dashboard/"},
            message="Sign in successful.",
            status_code=status.HTTP_200_OK,
        )


class RegisterViewSet(BaseViewSet):
    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    def _register_service(self):
        return RegisterService(user=self.request.user, request=self.request)

    @extend_schema(
        summary="Self-register a new account",
        description=(
            "Creates a new classic-auth user account. "
            "Requires AUTH_MODE=classic and ALLOW_REGISTRATION=true. "
            "Returns 409 if the email is already registered, "
            "403 if self-registration is disabled."
        ),
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description="Account created. Please sign in."),
            400: OpenApiResponse(
                description="Validation error — missing or malformed fields."
            ),
            403: OpenApiResponse(description="Self-registration is not enabled."),
            409: OpenApiResponse(
                description="An account with this email already exists."
            ),
            422: OpenApiResponse(
                description="Passwords do not match or password too weak."
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="register", url_name="register")
    def register(self, request: Request):
        """POST /auth/register/"""
        serializer = RegisterSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self._register_service().register(
            first_name=serializer.validated_data["first_name"],
            last_name=serializer.validated_data["last_name"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        return self.response(
            message="Account created successfully. Please sign in.",
            status_code=status.HTTP_201_CREATED,
        )


class ForgotPasswordViewSet(BaseViewSet):
    authentication_classes: list[type] = []
    permission_classes = [AllowAny]

    def _fp_service(self):
        return ForgotPasswordService(user=self.request.user, request=self.request)

    @extend_schema(
        summary="Request password reset",
        description=(
            "Sends a 6-digit reset code to the supplied email address. "
            "Returns 422 when no active account exists for the given email."
        ),
        request=ForgotPasswordRequestSerializer,
        responses={
            200: OpenApiResponse(description="Reset code dispatched."),
            400: OpenApiResponse(
                description="Validation error — email missing or malformed."
            ),
            422: OpenApiResponse(
                description="No account found for that email address."
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="request", url_name="fp-request")
    def request_reset(self, request: Request):
        """POST /auth/forgot-password/"""
        serializer = ForgotPasswordRequestSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self._fp_service().request_password_reset(
            email=serializer.validated_data["email"]
        )
        return self.response(
            message="If that email has an account, a reset code has been sent.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Verify reset code",
        description=(
            "Checks that the 6-digit code is valid and unexpired for the given email. "
            "The code is NOT consumed — a subsequent reset call is still required."
        ),
        request=ForgotPasswordVerifySerializer,
        responses={
            200: OpenApiResponse(description="Code is valid."),
            400: OpenApiResponse(
                description=(
                    "Code is invalid, expired, or the request payload is malformed."
                )
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="verify", url_name="fp-verify")
    def verify_code(self, request: Request):
        """POST /auth/forgot-password/verify/"""
        serializer = ForgotPasswordVerifySerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        is_valid = self._fp_service().verify_reset_code(
            email=serializer.validated_data["email"],
            code=serializer.validated_data["code"],
        )
        if not is_valid:
            raise ValidationException("Invalid or expired reset code.")
        return self.response(
            message="Code verified.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Reset password",
        description=(
            "Consumes the reset code and sets a new password. "
            "The new password must be strong (12+ chars, mixed case, digit, symbol) "
            "and must differ from the user's current password."
        ),
        request=ForgotPasswordResetSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successfully."),
            400: OpenApiResponse(
                description=(
                    "Invalid or expired code, passwords do not match, "
                    "new password is too weak, or same as current password."
                )
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="reset", url_name="fp-reset")
    def reset_password(self, request: Request):
        """POST /auth/forgot-password/reset/"""
        serializer = ForgotPasswordResetSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self._fp_service().reset_password(
            email=serializer.validated_data["email"],
            code=serializer.validated_data["code"],
            new_password=serializer.validated_data["new_password"],
        )
        return self.response(
            message="Password reset successfully. Please sign in.",
            status_code=status.HTTP_200_OK,
        )
