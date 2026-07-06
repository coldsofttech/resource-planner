from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    ResourcePlanVersionCreateSerializer,
    ResourcePlanVersionDetailSerializer,
    ResourcePlanVersionHistorySerializer,
)
from apps.resource_plans.services import ResourcePlanVersionService


@extend_schema(tags=["Resource Plans: Versions"])
class ResourcePlanVersionViewSet(BaseViewSet):
    service_class = ResourcePlanVersionService

    def get_permissions(self):
        action_perms = {
            "retrieve": "resource_plans.view_planversion",
            "create": "resource_plans.add_planversion",
            "destroy": "resource_plans.delete_planversion",
            "activate": "resource_plans.change_planversion",
            "restore": "resource_plans.change_planversion",
            "lock": "resource_plans.change_planversion",
            "history": "resource_plans.view_planversion",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Add a version to a resource plan",
        request=ResourcePlanVersionCreateSerializer,
        responses={
            201: ResourcePlanVersionDetailSerializer,
            404: OpenApiResponse(description="Resource plan not found."),
        },
    )
    def create(self, request: Request, code: str | None = None):
        """POST /resource-plans/<code>/versions/"""
        serializer = ResourcePlanVersionCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(plan_code=code, **serializer.validated_data)
        return self.response(
            data=ResourcePlanVersionDetailSerializer(obj).data,
            message="Version added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Retrieve a resource plan version",
        responses={
            200: ResourcePlanVersionDetailSerializer,
            404: OpenApiResponse(description="Version not found."),
        },
    )
    def retrieve(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET /resource-plans/<code>/versions/<version>/"""
        obj = self.service.get(plan_code=code, version=version)
        return self.response(
            data=ResourcePlanVersionDetailSerializer(obj).data,
            message="Version retrieved successfully.",
        )

    @extend_schema(
        summary="Delete a draft resource plan version",
        responses={
            204: OpenApiResponse(description="Version deleted successfully."),
            404: OpenApiResponse(description="Version not found."),
            422: OpenApiResponse(description="Only a draft version can be deleted."),
        },
    )
    def destroy(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """DELETE /resource-plans/<code>/versions/<version>/"""
        self.service.delete(plan_code=code, version=version)
        return self.response(
            message="Version deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Activate a resource plan version",
        responses={
            200: ResourcePlanVersionDetailSerializer,
            404: OpenApiResponse(description="Version not found."),
            422: OpenApiResponse(description="A locked version cannot be activated."),
        },
    )
    def activate(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """POST /resource-plans/<code>/versions/<version>/activate/"""
        obj = self.service.activate(plan_code=code, version=version)
        return self.response(
            data=ResourcePlanVersionDetailSerializer(obj).data,
            message="Version activated successfully.",
        )

    @extend_schema(
        summary="Restore a resource plan version as a new draft version",
        responses={
            201: ResourcePlanVersionDetailSerializer,
            404: OpenApiResponse(description="Version not found."),
        },
    )
    def restore(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """POST /resource-plans/<code>/versions/<version>/restore/"""
        obj = self.service.restore(plan_code=code, version=version)
        return self.response(
            data=ResourcePlanVersionDetailSerializer(obj).data,
            message="Version restored as a new version successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Lock an active resource plan version",
        responses={
            200: ResourcePlanVersionDetailSerializer,
            404: OpenApiResponse(description="Version not found."),
            422: OpenApiResponse(description="Only an active version can be locked."),
        },
    )
    def lock(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """POST /resource-plans/<code>/versions/<version>/lock/"""
        obj = self.service.lock(plan_code=code, version=version)
        return self.response(
            data=ResourcePlanVersionDetailSerializer(obj).data,
            message="Version locked successfully.",
        )

    @extend_schema(
        summary="List version history for a resource plan",
        responses={200: ResourcePlanVersionHistorySerializer(many=True)},
    )
    def history(self, request: Request, code: str | None = None):
        """GET /resource-plans/<code>/versions/history/"""
        rows = self.service.history(plan_code=code)
        data = ResourcePlanVersionHistorySerializer(rows, many=True).data
        return self.response(data=data, message="History retrieved successfully.")
