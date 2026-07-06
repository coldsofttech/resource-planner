from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    ResourcePlanCommentCreateSerializer,
    ResourcePlanCommentSerializer,
    ResourcePlanCommentUpdateSerializer,
)
from apps.resource_plans.services import ResourcePlanCommentService


@extend_schema(tags=["Resource Plans: Comments"])
class ResourcePlanCommentViewSet(BaseViewSet):
    service_class = ResourcePlanCommentService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_plancomment",
            "retrieve": "resource_plans.view_plancomment",
            "create": "resource_plans.add_plancomment",
            "partial_update": "resource_plans.change_plancomment",
            "destroy": "resource_plans.delete_plancomment",
            "pin": "resource_plans.change_plancomment",
            "unpin": "resource_plans.change_plancomment",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List comments for a resource plan",
        responses={200: ResourcePlanCommentSerializer(many=True)},
    )
    def list(self, request: Request, code: str | None = None):
        """GET /resource-plans/<code>/comments/"""
        page, page_size = self.get_pagination_params(request)
        result = self.service.list(plan_code=code, page=page, page_size=page_size)
        return self.paginated_response(
            result=result,
            serializer_class=ResourcePlanCommentSerializer,
            message="Comments retrieved successfully.",
        )

    @extend_schema(
        summary="Add a comment to a resource plan",
        request=ResourcePlanCommentCreateSerializer,
        responses={
            201: ResourcePlanCommentSerializer,
            404: OpenApiResponse(description="Resource plan not found."),
        },
    )
    def create(self, request: Request, code: str | None = None):
        """POST /resource-plans/<code>/comments/"""
        serializer = ResourcePlanCommentCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(plan_code=code, **serializer.validated_data)
        return self.response(
            data=ResourcePlanCommentSerializer(obj).data,
            message="Comment added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Retrieve a resource plan comment",
        responses={
            200: ResourcePlanCommentSerializer,
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def retrieve(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """GET /resource-plans/<code>/comments/<comment_code>/"""
        obj = self.service.get(code=comment_code)
        return self.response(
            data=ResourcePlanCommentSerializer(obj).data,
            message="Comment retrieved successfully.",
        )

    @extend_schema(
        summary="Update a resource plan comment",
        request=ResourcePlanCommentUpdateSerializer,
        responses={
            200: ResourcePlanCommentSerializer,
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def partial_update(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """PATCH /resource-plans/<code>/comments/<comment_code>/"""
        serializer = ResourcePlanCommentUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=comment_code, **serializer.validated_data)
        return self.response(
            data=ResourcePlanCommentSerializer(obj).data,
            message="Comment updated successfully.",
        )

    @extend_schema(
        summary="Delete a resource plan comment",
        responses={
            204: OpenApiResponse(description="Comment deleted successfully."),
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def destroy(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """DELETE /resource-plans/<code>/comments/<comment_code>/"""
        self.service.delete(code=comment_code)
        return self.response(
            message="Comment deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Pin a resource plan comment",
        responses={
            200: ResourcePlanCommentSerializer,
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def pin(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """POST /resource-plans/<code>/comments/<comment_code>/pin/"""
        obj = self.service.pin(code=comment_code)
        return self.response(
            data=ResourcePlanCommentSerializer(obj).data,
            message="Comment pinned successfully.",
        )

    @extend_schema(
        summary="Unpin a resource plan comment",
        responses={
            200: ResourcePlanCommentSerializer,
            404: OpenApiResponse(description="Comment not found."),
        },
    )
    def unpin(
        self, request: Request, code: str | None = None, comment_code: str | None = None
    ):
        """POST /resource-plans/<code>/comments/<comment_code>/unpin/"""
        obj = self.service.unpin(code=comment_code)
        return self.response(
            data=ResourcePlanCommentSerializer(obj).data,
            message="Comment unpinned successfully.",
        )
