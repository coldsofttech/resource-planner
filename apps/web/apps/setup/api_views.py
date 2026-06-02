import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from apps.core.viewsets import BaseViewSet
from apps.setup.serializers import (
    DbTestInputSerializer,
    EmailTestInputSerializer,
    GenerateKeySerializer,
    OAuthTestInputSerializer,
    SAMLTestInputSerializer,
    SetupDefaultsSerializer,
    SetupInputSerializer,
    SetupStatusSerializer,
)
from apps.setup.services import SetupService

logger = logging.getLogger(__name__)


class SetupViewSet(BaseViewSet):
    authentication_classes: list[type] = []
    permission_classes = [AllowAny]
    service_class = SetupService

    def _test_service(self):
        from apps.setup.services import TestService

        return TestService(user=self.request.user, request=self.request)

    def _status_service(self):
        from apps.setup import status as _status

        return _status

    def get_retrieve_serializer_class(self):
        return None

    def get_create_serializer_class(self):
        return SetupInputSerializer

    @extend_schema(
        summary="Retrieve setup defaults",
        responses={200: SetupDefaultsSerializer},
    )
    def list(self, request):
        """GET /setup/"""
        from pathlib import Path

        from django.conf import settings

        from apps.configurations.selectors import Setup

        base = Path(settings.BASE_DIR)
        data = {
            "setup_complete": Setup.get_setup_complete(),
            "defaults": {
                "app_name": "Resource<b>Planner</b>",
                "self_register": True,
                "storage_type": "filesystem",
                "storage_path": str(base / "media"),
                "log_name": "application",
                "log_path": str(base / "logs"),
                "log_rotation": "size",
                "log_rotation_size_mb": 10,
                "log_cleanup_keep_files": 10,
                "log_cleanup_keep_days": 5,
            },
        }
        logger.debug("Setup defaults requested.")
        serializer = SetupDefaultsSerializer(
            data, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    def get_create_custom_message(self):
        return "Setup completed successfully."

    @extend_schema(
        summary="Initial setup provider",
        request=SetupInputSerializer,
        responses={201: OpenApiResponse(description="Setup successful.")},
    )
    def create(self, request):
        """POST /setup/"""
        from apps.configurations.selectors import Setup
        from apps.core.exceptions import ConflictException

        if Setup.get_setup_complete():
            raise ConflictException("Setup has already been completed.")

        logger.info("Setup wizard submission received.")
        return super().create(request)

    @extend_schema(
        summary="Test PostgreSQL database connection",
        request=DbTestInputSerializer,
        responses={
            200: OpenApiResponse(description="Connection successful."),
            400: OpenApiResponse(description="Invalid request payload."),
            422: OpenApiResponse(
                description=(
                    "Connection test failed — check host, port, credentials, "
                    "or network access."
                )
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="test/db")
    def db_test(self, request):
        """POST /setup/test/db/"""
        logger.debug("Database connection test requested.")
        serializer = DbTestInputSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        self._test_service().test_db_connection(**serializer.validated_data)

        return self.response(
            message="Connection successful.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Test SAML IdP connection",
        request=SAMLTestInputSerializer,
        responses={
            200: OpenApiResponse(
                description="SAML IdP reachable and certificate valid."
            ),
            400: OpenApiResponse(description="Invalid request payload."),
            422: OpenApiResponse(
                description="Connection test failed — check IdP SSO URL or certificate."
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="test/saml")
    def saml_test(self, request):
        """POST /setup/test/saml/"""
        logger.debug("SAML connection test requested.")
        serializer = SAMLTestInputSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        self._test_service().test_saml_connection(**serializer.validated_data)

        return self.response(
            message="SAML IdP is reachable and the certificate is valid.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Test OAuth provider connection",
        request=OAuthTestInputSerializer,
        responses={
            200: OpenApiResponse(description="OAuth endpoints reachable."),
            400: OpenApiResponse(description="Invalid request payload."),
            422: OpenApiResponse(
                description=(
                    "Connection test failed — check endpoints or client credentials."
                )
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="test/oauth")
    def oauth_test(self, request):
        """POST /setup/test/oauth/"""
        logger.debug("OAuth connection test requested.")
        serializer = OAuthTestInputSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        self._test_service().test_oauth_connection(**serializer.validated_data)

        return self.response(
            message="OAuth endpoints are reachable.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Test email configuration",
        request=EmailTestInputSerializer,
        responses={
            200: OpenApiResponse(description="Test email sent."),
            400: OpenApiResponse(description="Invalid request payload."),
            422: OpenApiResponse(
                description=(
                    "Email test failed — check SMTP host, port, credentials, or "
                    "encryption settings."
                )
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="test/email")
    def email_test(self, request):
        """POST /setup/test/email/"""
        logger.debug("Email connection test requested.")
        serializer = EmailTestInputSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        self._test_service().test_email_connection(**serializer.validated_data)

        return self.response(
            message="Test email sent successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Setup progress status",
        responses={200: SetupStatusSerializer},
    )
    @action(detail=False, methods=["get"], url_path="status")
    def setup_status(self, request):
        """GET /setup/status/"""
        logger.debug("Setup status polled.")
        serializer = SetupStatusSerializer(
            self._status_service().get(), context=self.get_serializer_context()
        )

        return self.response(
            data=serializer.data,
            message="Status retrieved.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Generate Fernet key",
        responses={
            201: GenerateKeySerializer,
            500: OpenApiResponse(description="Key generation failed."),
        },
    )
    @action(detail=False, methods=["post"], url_path="gen-key")
    def gen_key(self, request):
        """POST /setup/gen-key/"""
        from pycore import generate_key

        key = generate_key()
        logger.info("Fernet key generated successfully.")
        serializer = GenerateKeySerializer(
            {"key": key},
            context=self.get_serializer_context(),
        )

        return self.response(
            data=serializer.data,
            message="Key generated.",
            status_code=status.HTTP_201_CREATED,
        )
