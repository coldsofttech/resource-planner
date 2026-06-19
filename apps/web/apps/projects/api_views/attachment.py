from __future__ import annotations

import urllib.parse

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.exceptions import ValidationException
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers.attachment import ProjectAttachmentSerializer
from apps.projects.services import ProjectAttachmentService


@extend_schema(tags=["Projects: Attachments"])
class ProjectAttachmentViewSet(BaseViewSet):
    service_class = ProjectAttachmentService

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectattachment",
            "create": "projects.add_projectattachment",
            "download": "projects.view_projectattachment",
            "destroy": "projects.delete_projectattachment",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List attachments for a project",
        responses={200: ProjectAttachmentSerializer(many=True)},
    )
    def list(self, request: Request, code=None):
        """GET /projects/<code>/attachments/"""
        params = self.get_list_params(request)
        attachments = self.service.list(project_code=code, params=params)
        data = ProjectAttachmentSerializer(attachments, many=True).data
        return self.response(data=data, message="Attachments retrieved successfully.")

    @extend_schema(
        summary="Upload an attachment to a project",
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
            201: ProjectAttachmentSerializer,
            400: OpenApiResponse(description="No file or file exceeds size limit."),
            409: OpenApiResponse(description="A file with this name already exists."),
        },
    )
    def create(self, request: Request, code=None):
        """POST /projects/<code>/attachments/"""
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationException("No file uploaded.")

        file_data = uploaded_file.read()
        obj = self.service.upload(
            project_code=code,
            file_data=file_data,
            file_name=uploaded_file.name or "attachment",
            content_type=uploaded_file.content_type or "",
            file_size=len(file_data),
        )
        return self.response(
            data=ProjectAttachmentSerializer(obj).data,
            message="Attachment uploaded successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Download an attachment",
        responses={
            200: OpenApiResponse(description="File binary content."),
            404: OpenApiResponse(description="Attachment not found."),
        },
    )
    def download(self, request: Request, code=None, attachment_code=None):
        """GET /projects/<code>/attachments/<attachment_code>/download/"""
        content, content_type, file_name = self.service.download(code=attachment_code)
        encoded_name = urllib.parse.quote(file_name.encode("utf-8"), safe="")
        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = (
            f"attachment; filename=\"{file_name}\"; filename*=UTF-8''{encoded_name}"
        )
        response["Content-Length"] = str(len(content))
        return response

    @extend_schema(
        summary="Delete an attachment",
        responses={
            204: OpenApiResponse(description="Attachment deleted."),
            404: OpenApiResponse(description="Attachment not found."),
        },
    )
    def destroy(self, request: Request, code=None, attachment_code=None):
        """DELETE /projects/<code>/attachments/<attachment_code>/"""
        self.service.delete(code=attachment_code)
        return self.response(
            message="Attachment deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
