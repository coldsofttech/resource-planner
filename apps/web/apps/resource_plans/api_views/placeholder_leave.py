from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    PlaceholderLeaveRegenerateSerializer,
    PlaceholderLeaveSerializer,
    PlaceholderLeaveUpdateSerializer,
)
from apps.resource_plans.services import PlaceholderLeaveService


@extend_schema(tags=["Resource Plans: Placeholder Leaves"])
class PlaceholderLeaveViewSet(BaseViewSet):
    service_class = PlaceholderLeaveService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_placeholderleave",
            "partial_update": "resource_plans.change_placeholderleave",
            "destroy": "resource_plans.delete_placeholderleave",
            "regenerate": "resource_plans.add_placeholderleave",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List placeholder leaves for a resource plan version",
        responses={200: PlaceholderLeaveSerializer(many=True)},
    )
    def list(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/placeholder-leaves/"""
        params = self.get_list_params(request)
        result = self.service.list_for_version(
            plan_code=code, version=version, params=params
        )
        return self.paginated_response(
            result=result,
            serializer_class=PlaceholderLeaveSerializer,
            message="Placeholder leaves retrieved successfully.",
        )

    @extend_schema(
        summary="Update a placeholder leave",
        request=PlaceholderLeaveUpdateSerializer,
        responses={
            200: PlaceholderLeaveSerializer,
            404: OpenApiResponse(description="Placeholder leave not found."),
        },
    )
    def partial_update(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        leave_code: str | None = None,
    ):
        """PATCH .../placeholder-leaves/<leave_code>/"""
        serializer = PlaceholderLeaveUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(
            plan_code=code,
            version=version,
            leave_code=leave_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlaceholderLeaveSerializer(obj).data,
            message="Placeholder leave updated successfully.",
        )

    @extend_schema(
        summary="Delete a placeholder leave",
        responses={
            204: OpenApiResponse(description="Placeholder leave removed successfully."),
            404: OpenApiResponse(description="Placeholder leave not found."),
        },
    )
    def destroy(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        leave_code: str | None = None,
    ):
        """DELETE .../placeholder-leaves/<leave_code>/"""
        self.service.delete(plan_code=code, version=version, leave_code=leave_code)
        return self.response(
            message="Placeholder leave removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Regenerate auto-generated placeholder leaves for a version",
        request=PlaceholderLeaveRegenerateSerializer,
        responses={200: OpenApiResponse(description="Regeneration summary.")},
    )
    def regenerate(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """POST .../placeholder-leaves/regenerate/"""
        serializer = PlaceholderLeaveRegenerateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        created_count = self.service.regenerate(
            plan_code=code, version=version, **serializer.validated_data
        )
        return self.response(
            data={"regenerated_count": created_count},
            message="Placeholder leaves regenerated successfully.",
        )
