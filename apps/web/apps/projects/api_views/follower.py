from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers import (
    ProjectFollowerListSerializer,
    ProjectFollowerUpdateSerializer,
)
from apps.projects.services import ProjectFollowerService


@extend_schema(tags=["Projects"])
class ProjectFollowerViewSet(BaseViewSet):
    service_class = ProjectFollowerService

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectfollower",
            "retrieve": "projects.view_projectfollower",
            "create": "projects.add_projectfollower",
            "partial_update": "projects.change_projectfollower",
            "destroy": "projects.delete_projectfollower",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List followers for a project",
        responses={200: ProjectFollowerListSerializer(many=True)},
    )
    def list(self, request: Request, code=None):
        """GET /projects/<code>/followers/"""
        followers = self.service.list(project_code=code)
        data = ProjectFollowerListSerializer(followers, many=True).data
        return self.response(data=data, message="Followers retrieved successfully.")

    @extend_schema(
        summary="Retrieve a project follower",
        responses={
            200: ProjectFollowerListSerializer,
            404: OpenApiResponse(description="Follower not found."),
        },
    )
    def retrieve(self, request: Request, code=None, follower_code=None):
        """GET /projects/<code>/followers/<follower_code>/"""
        obj = self.service.get(code=follower_code)
        return self.response(data=ProjectFollowerListSerializer(obj).data)

    @extend_schema(
        summary="Add a follower to a project",
        responses={
            201: ProjectFollowerListSerializer,
            404: OpenApiResponse(description="Project not found."),
            409: OpenApiResponse(description="User is already following this project."),
        },
    )
    def create(self, request: Request, code=None):
        """POST /projects/<code>/followers/"""
        user_code = getattr(getattr(request.user, "profile", None), "code", None)
        obj = self.service.create(project_code=code, user_code=user_code)
        return self.response(
            data=ProjectFollowerListSerializer(obj).data,
            message="Follower added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a project follower",
        request=ProjectFollowerUpdateSerializer,
        responses={
            200: ProjectFollowerListSerializer,
            404: OpenApiResponse(description="Follower or user not found."),
            409: OpenApiResponse(description="User is already following this project."),
        },
    )
    def partial_update(self, request: Request, code=None, follower_code=None):
        """PATCH /projects/<code>/followers/<follower_code>/"""
        serializer = ProjectFollowerUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=follower_code, **serializer.validated_data)
        return self.response(
            data=ProjectFollowerListSerializer(obj).data,
            message="Follower updated successfully.",
        )

    @extend_schema(
        summary="Remove a follower from a project",
        responses={
            204: OpenApiResponse(description="Follower removed successfully."),
            404: OpenApiResponse(description="Follower not found."),
        },
    )
    def destroy(self, request: Request, code=None, follower_code=None):
        """DELETE /projects/<code>/followers/<follower_code>/"""
        self.service.delete(code=follower_code)
        return self.response(
            message="Follower removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
