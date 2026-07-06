from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, StatisticsMixin
from apps.resource_plans.serializers import (
    ResourcePlanCreateSerializer,
    ResourcePlanDetailSerializer,
    ResourcePlanListSerializer,
    ResourcePlanUpdateSerializer,
)
from apps.resource_plans.services import ResourcePlanService


@extend_schema(tags=["Resource Plans"])
class ResourcePlanViewSet(StatisticsMixin, BaseViewSet):
    service_class = ResourcePlanService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_plan",
            "retrieve": "resource_plans.view_plan",
            "options": "resource_plans.view_plan",
            "statistics": "resource_plans.view_plan",
            "create": "resource_plans.add_plan",
            "partial_update": "resource_plans.change_plan",
            "destroy": "resource_plans.delete_plan",
            "activate": "resource_plans.change_plan",
            "deactivate": "resource_plans.change_plan",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return ResourcePlanListSerializer

    def get_retrieve_serializer_class(self):
        return ResourcePlanDetailSerializer

    def get_create_serializer_class(self):
        return ResourcePlanCreateSerializer

    def get_update_serializer_class(self):
        return ResourcePlanUpdateSerializer

    def get_create_response_serializer_class(self):
        return ResourcePlanDetailSerializer

    @extend_schema(
        summary="List resource plan options",
        responses={
            200: OpenApiResponse(description="List of active resource plan options.")
        },
    )
    def options(self, request: Request):
        """GET /resource-plans/options/"""
        return self.response(
            data=self.service.options(),
            message="Resource plan options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List resource plans",
        responses={200: ResourcePlanListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /resource-plans/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a resource plan",
        responses={
            200: ResourcePlanDetailSerializer,
            404: OpenApiResponse(description="Resource plan not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /resource-plans/<code>/"""
        obj = self.service.get(code=code)
        serializer = ResourcePlanDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a resource plan",
        request=ResourcePlanCreateSerializer,
        responses={
            201: ResourcePlanDetailSerializer,
            409: OpenApiResponse(
                description="A resource plan with this name already exists."
            ),
        },
    )
    def create(self, request: Request):
        """POST /resource-plans/"""
        return super().create(request)

    @extend_schema(
        summary="Update a resource plan",
        request=ResourcePlanUpdateSerializer,
        responses={
            200: ResourcePlanDetailSerializer,
            404: OpenApiResponse(description="Resource plan not found."),
            409: OpenApiResponse(
                description="A resource plan with this name already exists."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /resource-plans/<code>/"""
        serializer = ResourcePlanUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = ResourcePlanDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a resource plan",
        responses={
            204: OpenApiResponse(description="Resource plan deleted successfully."),
            404: OpenApiResponse(description="Resource plan not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /resource-plans/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a resource plan",
        responses={
            200: ResourcePlanDetailSerializer,
            404: OpenApiResponse(description="Resource plan not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /resource-plans/<code>/activate/"""
        obj = self.service.activate(code=code)
        data = ResourcePlanDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a resource plan",
        responses={
            200: ResourcePlanDetailSerializer,
            404: OpenApiResponse(description="Resource plan not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /resource-plans/<code>/deactivate/"""
        obj = self.service.deactivate(code=code)
        data = ResourcePlanDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )
