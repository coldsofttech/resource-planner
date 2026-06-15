from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers import (
    ProjectTagCreateSerializer,
    ProjectTagSerializer,
    ProjectTagUpdateSerializer,
)
from apps.projects.services import ProjectTagService


@extend_schema(tags=["Projects: Tags"])
class ProjectTagViewSet(BaseViewSet):
    service_class = ProjectTagService

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projecttag",
            "retrieve": "projects.view_projecttag",
            "create": "projects.add_projecttag",
            "partial_update": "projects.change_projecttag",
            "destroy": "projects.delete_projecttag",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List tags for a project",
        responses={200: ProjectTagSerializer(many=True)},
    )
    def list(self, request: Request, code=None):
        """GET /projects/<code>/tags/"""
        tags = self.service.list(project_code=code)
        data = ProjectTagSerializer(tags, many=True).data
        return self.response(data=data, message="Tags retrieved successfully.")

    @extend_schema(
        summary="Retrieve a project tag",
        responses={
            200: ProjectTagSerializer,
            404: OpenApiResponse(description="Project tag not found."),
        },
    )
    def retrieve(self, request: Request, code=None, tag_code=None):
        """GET /projects/<code>/tags/<tag_code>/"""
        obj = self.service.get(code=tag_code)
        return self.response(data=ProjectTagSerializer(obj).data)

    @extend_schema(
        summary="Add a tag to a project",
        request=ProjectTagCreateSerializer,
        responses={
            201: ProjectTagSerializer,
            404: OpenApiResponse(description="Project or tag not found."),
            409: OpenApiResponse(description="Tag already assigned to this project."),
        },
    )
    def create(self, request: Request, code=None):
        """POST /projects/<code>/tags/"""
        serializer = ProjectTagCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(project_code=code, **serializer.validated_data)
        return self.response(
            data=ProjectTagSerializer(obj).data,
            message="Tag added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update the tag on a project tag entry",
        request=ProjectTagUpdateSerializer,
        responses={
            200: ProjectTagSerializer,
            404: OpenApiResponse(description="Project tag or tag not found."),
            409: OpenApiResponse(description="Tag already assigned to this project."),
        },
    )
    def partial_update(self, request: Request, code=None, tag_code=None):
        """PATCH /projects/<code>/tags/<tag_code>/"""
        serializer = ProjectTagUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=tag_code, **serializer.validated_data)
        return self.response(
            data=ProjectTagSerializer(obj).data,
            message="Tag updated successfully.",
        )

    @extend_schema(
        summary="Remove a tag from a project",
        responses={
            204: OpenApiResponse(description="Tag removed successfully."),
            404: OpenApiResponse(description="Project tag not found."),
        },
    )
    def destroy(self, request: Request, code=None, tag_code=None):
        """DELETE /projects/<code>/tags/<tag_code>/"""
        self.service.delete(code=tag_code)
        return self.response(
            message="Tag removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
