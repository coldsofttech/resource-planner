from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers import (
    ProjectContactCreateSerializer,
    ProjectContactSerializer,
)
from apps.projects.services import ProjectContactService


@extend_schema(tags=["Projects: Contacts"])
class ProjectContactViewSet(BaseViewSet):
    service_class = ProjectContactService

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectcontact",
            "create": "projects.add_projectcontact",
            "destroy": "projects.delete_projectcontact",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List contacts for a project",
        responses={200: ProjectContactSerializer(many=True)},
    )
    def list(self, request: Request, code: str | None = None):
        """GET /projects/<code>/contacts/"""
        contacts = self.service.list(project_code=code)
        data = ProjectContactSerializer(contacts, many=True).data
        return self.response(data=data, message="Contacts retrieved successfully.")

    @extend_schema(
        summary="Add a contact to a project",
        request=ProjectContactCreateSerializer,
        responses={
            201: ProjectContactSerializer,
            404: OpenApiResponse(description="Project not found."),
            409: OpenApiResponse(
                description="Contact already assigned to this project."
            ),
        },
    )
    def create(self, request: Request, code: str | None = None):
        """POST /projects/<code>/contacts/"""
        serializer = ProjectContactCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(project_code=code, **serializer.validated_data)
        return self.response(
            data=ProjectContactSerializer(obj).data,
            message="Contact added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Remove a contact from a project",
        responses={
            204: OpenApiResponse(description="Contact removed successfully."),
            404: OpenApiResponse(description="Project contact not found."),
        },
    )
    def destroy(
        self, request: Request, code: str | None = None, contact_code: str | None = None
    ):
        """DELETE /projects/<code>/contacts/<contact_code>/"""
        self.service.delete(code=contact_code)
        return self.response(
            message="Contact removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
