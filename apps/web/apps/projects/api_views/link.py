from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers.link import (
    ProjectLinkCreateSerializer,
    ProjectLinkSerializer,
    ProjectLinkUpdateSerializer,
)
from apps.projects.services import ProjectLinkService


@extend_schema(tags=["Projects: Links"])
class ProjectLinkViewSet(BaseViewSet):
    service_class = ProjectLinkService

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectlink",
            "retrieve": "projects.view_projectlink",
            "create": "projects.add_projectlink",
            "partial_update": "projects.change_projectlink",
            "destroy": "projects.delete_projectlink",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List links for a project",
        responses={200: ProjectLinkSerializer(many=True)},
    )
    def list(self, request: Request, code=None):
        """GET /projects/<code>/links/"""
        links = self.service.list(project_code=code)
        data = ProjectLinkSerializer(links, many=True).data
        return self.response(data=data, message="Links retrieved successfully.")

    @extend_schema(
        summary="Retrieve a project link",
        responses={
            200: ProjectLinkSerializer,
            404: OpenApiResponse(description="Link not found."),
        },
    )
    def retrieve(self, request: Request, code=None, link_code=None):
        """GET /projects/<code>/links/<link_code>/"""
        obj = self.service.get(code=link_code)
        return self.response(data=ProjectLinkSerializer(obj).data)

    @extend_schema(
        summary="Add a link to a project",
        request=ProjectLinkCreateSerializer,
        responses={
            201: ProjectLinkSerializer,
            400: OpenApiResponse(description="Validation error."),
            409: OpenApiResponse(description="A link with this title already exists."),
        },
    )
    def create(self, request: Request, code=None):
        """POST /projects/<code>/links/"""
        serializer = ProjectLinkCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(project_code=code, **serializer.validated_data)
        return self.response(
            data=ProjectLinkSerializer(obj).data,
            message="Link added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a project link",
        request=ProjectLinkUpdateSerializer,
        responses={
            200: ProjectLinkSerializer,
            404: OpenApiResponse(description="Link not found."),
            409: OpenApiResponse(description="A link with this title already exists."),
        },
    )
    def partial_update(self, request: Request, code=None, link_code=None):
        """PATCH /projects/<code>/links/<link_code>/"""
        serializer = ProjectLinkUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=link_code, **serializer.validated_data)
        return self.response(
            data=ProjectLinkSerializer(obj).data,
            message="Link updated successfully.",
        )

    @extend_schema(
        summary="Delete a project link",
        responses={
            204: OpenApiResponse(description="Link deleted."),
            404: OpenApiResponse(description="Link not found."),
        },
    )
    def destroy(self, request: Request, code=None, link_code=None):
        """DELETE /projects/<code>/links/<link_code>/"""
        self.service.delete(code=link_code)
        return self.response(
            message="Link deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
