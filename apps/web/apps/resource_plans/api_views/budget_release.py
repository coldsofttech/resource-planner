from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    PlanBudgetReleaseCreateSerializer,
    PlanBudgetReleaseSerializer,
    PlanBudgetReleaseUpdateSerializer,
)
from apps.resource_plans.services import PlanBudgetReleaseService


@extend_schema(tags=["Resource Plans: Budget Releases"])
class PlanBudgetReleaseViewSet(BaseViewSet):
    service_class = PlanBudgetReleaseService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_planbudgetrelease",
            "create": "resource_plans.add_planbudgetrelease",
            "partial_update": "resource_plans.change_planbudgetrelease",
            "destroy": "resource_plans.delete_planbudgetrelease",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List budget releases for a plan version project",
        responses={200: PlanBudgetReleaseSerializer(many=True)},
    )
    def list(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
    ):
        """GET .../projects/<project_version_code>/budget-releases/"""
        releases = self.service.list_for_project(
            plan_code=code, version=version, project_version_code=project_version_code
        )
        return self.response(
            data=PlanBudgetReleaseSerializer(releases, many=True).data,
            message="Budget releases retrieved successfully.",
        )

    @extend_schema(
        summary="Add a budget release to a plan version project",
        request=PlanBudgetReleaseCreateSerializer,
        responses={
            201: PlanBudgetReleaseSerializer,
            404: OpenApiResponse(
                description="Plan, version, project, or sprint not found."
            ),
            409: OpenApiResponse(description="Duplicate budget release."),
            422: OpenApiResponse(description="Validation failed."),
        },
    )
    def create(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
    ):
        """POST .../projects/<project_version_code>/budget-releases/"""
        serializer = PlanBudgetReleaseCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanBudgetReleaseSerializer(obj).data,
            message="Budget release added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a budget release",
        request=PlanBudgetReleaseUpdateSerializer,
        responses={
            200: PlanBudgetReleaseSerializer,
            404: OpenApiResponse(description="Budget release or sprint not found."),
            409: OpenApiResponse(description="Duplicate budget release."),
            422: OpenApiResponse(description="Validation failed."),
        },
    )
    def partial_update(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
        budget_release_version_code: str | None = None,
    ):
        """PATCH .../budget-releases/<budget_release_version_code>/"""
        serializer = PlanBudgetReleaseUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            budget_release_version_code=budget_release_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanBudgetReleaseSerializer(obj).data,
            message="Budget release updated successfully.",
        )

    @extend_schema(
        summary="Remove a budget release",
        responses={
            204: OpenApiResponse(description="Budget release removed successfully."),
            404: OpenApiResponse(description="Budget release not found."),
        },
    )
    def destroy(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
        budget_release_version_code: str | None = None,
    ):
        """DELETE .../budget-releases/<budget_release_version_code>/"""
        self.service.delete(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            budget_release_version_code=budget_release_version_code,
        )
        return self.response(
            message="Budget release removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
