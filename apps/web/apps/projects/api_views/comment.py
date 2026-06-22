from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers import (
    ProjectCommentCreateSerializer,
    ProjectCommentSerializer,
    ProjectCommentUpdateSerializer,
)
from apps.projects.services import ProjectCommentService


@extend_schema(tags=["Projects: Comments"])
class ProjectCommentViewSet(BaseViewSet):
    service_class = ProjectCommentService

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectcomment",
            "retrieve": "projects.view_projectcomment",
            "create": "projects.add_projectcomment",
            "partial_update": "projects.change_projectcomment",
            "destroy": "projects.delete_projectcomment",
            "pin": "projects.change_projectcomment",
            "unpin": "projects.change_projectcomment",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List comments for a project",
        responses={200: ProjectCommentSerializer(many=True)},
    )
    def list(self, request: Request, code: str | None = None):
        """GET /projects/<code>/comments/"""
        page, page_size = self.get_pagination_params(request)
        result = self.service.list(project_code=code, page=page, page_size=page_size)
        return self.paginated_response(
            result=result,
            serializer_class=ProjectCommentSerializer,
            message="Comments retrieved successfully.",
        )

    @extend_schema(
        summary="Add a comment to a project",
        request=ProjectCommentCreateSerializer,
        responses={
            201: ProjectCommentSerializer,
            404: OpenApiResponse(description="Project not found."),
        },
    )
    def create(self, request: Request, code: str | None = None):
        """POST /projects/<code>/comments/"""
        serializer = ProjectCommentCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(project_code=code, **serializer.validated_data)
        return self.response(
            data=ProjectCommentSerializer(obj).data,
            message="Comment added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Retrieve a project comment",
        responses={
            200: ProjectCommentSerializer,
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def retrieve(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """GET /projects/<code>/comments/<comment_code>/"""
        obj = self.service.get(code=comment_code)
        return self.response(
            data=ProjectCommentSerializer(obj).data,
            message="Comment retrieved successfully.",
        )

    @extend_schema(
        summary="Update a project comment",
        request=ProjectCommentUpdateSerializer,
        responses={
            200: ProjectCommentSerializer,
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def partial_update(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """PATCH /projects/<code>/comments/<comment_code>/"""
        serializer = ProjectCommentUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=comment_code, **serializer.validated_data)
        return self.response(
            data=ProjectCommentSerializer(obj).data,
            message="Comment updated successfully.",
        )

    @extend_schema(
        summary="Delete a project comment",
        responses={
            204: OpenApiResponse(description="Comment deleted successfully."),
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def destroy(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """DELETE /projects/<code>/comments/<comment_code>/"""
        self.service.delete(code=comment_code)
        return self.response(
            message="Comment deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Pin a project comment",
        responses={
            200: ProjectCommentSerializer,
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def pin(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """POST /projects/<code>/comments/<comment_code>/pin/"""
        obj = self.service.pin(code=comment_code)
        return self.response(
            data=ProjectCommentSerializer(obj).data,
            message="Comment pinned successfully.",
        )

    @extend_schema(
        summary="Unpin a project comment",
        responses={
            200: ProjectCommentSerializer,
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def unpin(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """POST /projects/<code>/comments/<comment_code>/unpin/"""
        obj = self.service.unpin(code=comment_code)
        return self.response(
            data=ProjectCommentSerializer(obj).data,
            message="Comment unpinned successfully.",
        )
