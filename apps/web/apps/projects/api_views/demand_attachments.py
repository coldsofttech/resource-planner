from __future__ import annotations

import urllib.parse

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.auth.authentication import BearerTokenAuthentication
from apps.core.exceptions import ValidationException
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers.onboarding import OnboardingAttachmentSerializer
from apps.projects.services import OnboardingAttachmentService


@extend_schema(tags=["Demands"])
class DemandAttachmentViewSet(BaseViewSet):
    """Authenticated viewset for managing attachments on demand requests.

    Provides list, upload (reviewer-side), download, and delete.
    Public upload is handled by OnboardingAttachmentUploadViewSet.
    """

    def get_authenticators(self):
        return [BearerTokenAuthentication(), SessionAuthentication()]

    def get_permissions(self):
        return [IsAuthenticated()]

    @extend_schema(
        summary="List attachments for a demand request",
        responses={200: OnboardingAttachmentSerializer(many=True)},
    )
    def list(self, request: Request, code=None):
        """GET /demands/<code>/attachments/"""
        svc = OnboardingAttachmentService()
        attachments = svc.list(onboarding_code=code)
        return self.response(
            data=OnboardingAttachmentSerializer(attachments, many=True).data,
            message="Attachments retrieved successfully.",
        )

    @extend_schema(
        summary="Upload an attachment to a demand request (reviewer)",
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
        },
    )
    def create(self, request: Request, code=None):
        """POST /demands/<code>/attachments/"""
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

    @extend_schema(
        summary="Download an attachment from a demand request",
        responses={
            200: OpenApiResponse(description="File binary content."),
            404: OpenApiResponse(description="Attachment not found."),
        },
    )
    def download(
        self,
        request: Request,
        code=None,
        attachment_code=None,
    ):
        """GET /demands/<code>/attachments/<attachment_code>/download/"""
        svc = OnboardingAttachmentService()
        content, content_type, file_name = svc.download(code=attachment_code)
        encoded_name = urllib.parse.quote(file_name.encode("utf-8"), safe="")
        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = (
            f"attachment; filename=\"{file_name}\"; filename*=UTF-8''{encoded_name}"
        )
        response["Content-Length"] = str(len(content))
        return response

    @extend_schema(
        summary="Delete an attachment from a demand request",
        responses={
            204: OpenApiResponse(description="Attachment deleted."),
            404: OpenApiResponse(description="Attachment not found."),
        },
    )
    def destroy(
        self,
        request: Request,
        code=None,
        attachment_code=None,
    ):
        """DELETE /demands/<code>/attachments/<attachment_code>/"""
        svc = OnboardingAttachmentService()
        svc.delete(code=attachment_code)
        return self.response(
            message="Attachment deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
