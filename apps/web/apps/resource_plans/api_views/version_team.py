from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    PlanVersionTeamCreateSerializer,
    PlanVersionTeamSerializer,
    PlanVersionTeamUpdateSerializer,
)
from apps.resource_plans.services import PlanVersionTeamService


@extend_schema(tags=["Resource Plans: Version Teams"])
class PlanVersionTeamViewSet(BaseViewSet):
    service_class = PlanVersionTeamService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_planversionteam",
            "create": "resource_plans.add_planversionteam",
            "partial_update": "resource_plans.change_planversionteam",
            "destroy": "resource_plans.delete_planversionteam",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List teams assigned to a plan version project",
        responses={200: PlanVersionTeamSerializer(many=True)},
    )
    def list(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
    ):
        """GET .../projects/<project_version_code>/teams/"""
        teams = self.service.list_for_project(
            plan_code=code, version=version, project_version_code=project_version_code
        )
        return self.response(
            data=PlanVersionTeamSerializer(teams, many=True).data,
            message="Teams retrieved successfully.",
        )

    @extend_schema(
        summary="Assign a team to a plan version project",
        request=PlanVersionTeamCreateSerializer,
        responses={
            201: PlanVersionTeamSerializer,
            404: OpenApiResponse(
                description="Plan, version, project, or team not found."
            ),
            409: OpenApiResponse(description="Team already assigned to this project."),
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
        """POST .../projects/<project_version_code>/teams/"""
        serializer = PlanVersionTeamCreateSerializer(
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
            data=PlanVersionTeamSerializer(obj).data,
            message="Team assigned successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a team's allocation on a plan version project",
        request=PlanVersionTeamUpdateSerializer,
        responses={
            200: PlanVersionTeamSerializer,
            404: OpenApiResponse(description="Team assignment not found."),
            422: OpenApiResponse(description="Validation failed."),
        },
    )
    def partial_update(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
        team_version_code: str | None = None,
    ):
        """PATCH .../projects/<project_version_code>/teams/<team_version_code>/"""
        serializer = PlanVersionTeamUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanVersionTeamSerializer(obj).data,
            message="Team allocation updated successfully.",
        )

    @extend_schema(
        summary="Remove a team from a plan version project",
        responses={
            204: OpenApiResponse(description="Team removed successfully."),
            404: OpenApiResponse(description="Team assignment not found."),
        },
    )
    def destroy(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
        team_version_code: str | None = None,
    ):
        """DELETE .../projects/<project_version_code>/teams/<team_version_code>/"""
        self.service.delete(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
        )
        return self.response(
            message="Team removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
