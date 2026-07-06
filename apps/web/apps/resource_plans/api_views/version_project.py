from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    PlanVersionProjectConfigSerializer,
    PlanVersionProjectConfigUpdateSerializer,
    PlanVersionProjectCreateSerializer,
    PlanVersionProjectDetailSerializer,
    PlanVersionProjectListSerializer,
    ProjectBudgetLookupSerializer,
    UnmappedProjectSerializer,
)
from apps.resource_plans.services import PlanVersionProjectService


@extend_schema(tags=["Resource Plans: Version Projects"])
class PlanVersionProjectViewSet(BaseViewSet):
    service_class = PlanVersionProjectService

    def get_permissions(self):
        action_perms = {
            "unmapped": "resource_plans.view_planversionproject",
            "budget": "resource_plans.view_planversionproject",
            "create": "resource_plans.add_planversionproject",
            "list": "resource_plans.view_planversionproject",
            "retrieve": "resource_plans.view_planversionproject",
            "destroy": "resource_plans.delete_planversionproject",
            "resync": "resource_plans.change_planversionproject",
            "partial_update": "resource_plans.change_planversionproject",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List unmapped projects for a resource plan version",
        responses={200: UnmappedProjectSerializer(many=True)},
    )
    def unmapped(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET /resource-plans/<code>/versions/<version>/projects/unmapped/"""
        params = self.get_list_params(request)
        result = self.service.list_unmapped(
            plan_code=code, version=version, params=params
        )
        return self.paginated_response(
            result=result,
            serializer_class=UnmappedProjectSerializer,
            message="Unmapped projects retrieved successfully.",
        )

    @extend_schema(
        summary="Look up the available budget for a project in the plan's FY",
        parameters=[
            OpenApiParameter(
                name="project",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Project code to look up the budget for.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Budget data if configured, otherwise null."
            )
        },
    )
    def budget(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET /resource-plans/<code>/versions/<version>/projects/budget/"""
        project_code = request.query_params.get("project", "")
        budget = self.service.get_budget_for_project(
            plan_code=code, version=version, project_code=project_code
        )
        data = ProjectBudgetLookupSerializer(budget).data if budget else None
        return self.response(data=data, message="Success")

    @extend_schema(
        summary="Add a project to a resource plan version",
        request=PlanVersionProjectCreateSerializer,
        responses={
            201: PlanVersionProjectDetailSerializer,
            404: OpenApiResponse(description="Plan, version, or project not found."),
            409: OpenApiResponse(description="Project already mapped to this version."),
            422: OpenApiResponse(description="Validation failed."),
        },
    )
    def create(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """POST /resource-plans/<code>/versions/<version>/projects/"""
        serializer = PlanVersionProjectCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(
            plan_code=code, version=version, **serializer.validated_data
        )
        return self.response(
            data=PlanVersionProjectDetailSerializer(obj).data,
            message="Project added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="List projects configured on a resource plan version",
        responses={200: PlanVersionProjectListSerializer(many=True)},
    )
    def list(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET /resource-plans/<code>/versions/<version>/projects/"""
        params = self.get_list_params(request)
        result = self.service.list_configured(
            plan_code=code, version=version, params=params
        )
        return self.paginated_response(
            result=result,
            serializer_class=PlanVersionProjectListSerializer,
            message="Configured projects retrieved successfully.",
        )

    @extend_schema(
        summary="Get project configuration for a resource plan version",
        responses={
            200: PlanVersionProjectConfigSerializer,
            404: OpenApiResponse(description="Project mapping not found."),
        },
    )
    def retrieve(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
    ):
        """GET .../projects/<project_version_code>/"""
        obj = self.service.get(
            plan_code=code, version=version, project_version_code=project_version_code
        )
        return self.response(
            data=PlanVersionProjectConfigSerializer(obj).data,
            message="Success",
        )

    @extend_schema(
        summary="Update project configuration for a resource plan version",
        request=PlanVersionProjectConfigUpdateSerializer,
        responses={
            200: PlanVersionProjectConfigSerializer,
            404: OpenApiResponse(description="Project mapping not found."),
            422: OpenApiResponse(description="Validation failed."),
        },
    )
    def partial_update(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
    ):
        """PATCH .../projects/<project_version_code>/"""
        serializer = PlanVersionProjectConfigUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update_config(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanVersionProjectConfigSerializer(obj).data,
            message="Project configuration updated successfully.",
        )

    @extend_schema(
        summary="Remove a project from a resource plan version",
        responses={
            204: OpenApiResponse(description="Project removed successfully."),
            404: OpenApiResponse(description="Project mapping not found."),
        },
    )
    def destroy(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
    ):
        """DELETE .../projects/<project_version_code>/"""
        self.service.delete(
            plan_code=code, version=version, project_version_code=project_version_code
        )
        return self.response(
            message="Project removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Resync a project's basis amount from its live Budget/Estimate",
        responses={
            200: PlanVersionProjectDetailSerializer,
            404: OpenApiResponse(description="Project mapping not found."),
            422: OpenApiResponse(description="Project is already up to date."),
        },
    )
    def resync(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
    ):
        """POST .../projects/<project_version_code>/resync/"""
        obj = self.service.resync(
            plan_code=code, version=version, project_version_code=project_version_code
        )
        return self.response(
            data=PlanVersionProjectDetailSerializer(obj).data,
            message="Project resynced successfully.",
        )
