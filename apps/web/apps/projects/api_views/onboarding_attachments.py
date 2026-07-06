from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from apps.core.exceptions import ValidationException
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers.onboarding import OnboardingAttachmentSerializer
from apps.projects.services import OnboardingAttachmentService


@extend_schema(tags=["Onboarding"])
class OnboardingAttachmentUploadViewSet(BaseViewSet):
    """Public viewset for uploading attachments to a submitted demand request.

    Authentication is not required — the onboarding code acts as the key.
    Only upload is permitted; download and deletion are authenticated-only
    (DemandAttachmentViewSet).
    """

    def get_authenticators(self):
        return []

    def get_permissions(self):
        return [AllowAny()]

    @extend_schema(
        summary="Upload an attachment to a demand request (public)",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "File to attach (max 25 MB).",
                    }
                },
                "required": ["file"],
            }
        },
        responses={
            201: OnboardingAttachmentSerializer,
            400: OpenApiResponse(description="No file or file exceeds size limit."),
            409: OpenApiResponse(description="A file with this name already exists."),
            404: OpenApiResponse(description="Demand request not found."),
        },
    )
    def create(self, request: Request, code: str | None = None):
        """POST /onboarding/<code>/attachments/"""
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationException("No file uploaded.")

        file_data = uploaded_file.read()
        svc = OnboardingAttachmentService()
        obj = svc.upload(
            onboarding_code=code,
            file_data=file_data,
            file_name=uploaded_file.name or "attachment",
            content_type=uploaded_file.content_type or "",
            file_size=len(file_data),
        )
        return self.response(
            data=OnboardingAttachmentSerializer(obj).data,
            message="Attachment uploaded successfully.",
            status_code=status.HTTP_201_CREATED,
        )
