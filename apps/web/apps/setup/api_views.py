from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action

from apps.core.viewsets import BaseViewSet
from apps.setup.serializers import (
    DbTestInputSerializer,
    EmailTestInputSerializer,
    GenerateKeySerializer,
    SetupDefaultsSerializer,
    SetupInputSerializer,
    SetupStatusSerializer,
)
from apps.setup.services import SetupService, TestService


class SetupViewSet(BaseViewSet):
    service_class = SetupService

    def _test_service(self):
        return TestService(user=self.request.user, request=self.request)

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

        base = Path(settings.BASE_DIR)
        defaults = {
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
        }
        serializer = SetupDefaultsSerializer(
            defaults, context=self.get_serializer_context()
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
        return super().create(request)

    @extend_schema(
        summary="Test PostgreSQL database connection",
        request=DbTestInputSerializer,
        responses={200: OpenApiResponse(description="Connection successful.")},
    )
    @action(detail=False, methods=["post"], url_path="test/db")
    def db_test(self, request):
        """POST /setup/test/db/"""
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
        summary="Test email configuration",
        request=EmailTestInputSerializer,
        responses={200: OpenApiResponse(description="Test email sent.")},
    )
    @action(detail=False, methods=["post"], url_path="test/email")
    def email_test(self, request):
        """POST /setup/test/email/"""
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
        from apps.setup import status as _status

        serializer = SetupStatusSerializer(
            _status.get(), context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(summary="Generate Fernet key", responses=GenerateKeySerializer)
    @action(detail=False, methods=["post"], url_path="gen-key")
    def gen_key(self, request):
        """POST /setup/gen-key/"""
        from pycore import generate_key

        key = generate_key()
        serializer = GenerateKeySerializer(
            {"key": key},
            context=self.get_serializer_context(),
        )

        return self.response(
            data=serializer.data,
            message="Key generated.",
            status_code=status.HTTP_201_CREATED,
        )
