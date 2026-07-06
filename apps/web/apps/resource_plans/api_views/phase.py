from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    PlanPhaseCreateSerializer,
    PlanPhaseSerializer,
    PlanPhaseUpdateSerializer,
)
from apps.resource_plans.services import PlanPhaseService


@extend_schema(tags=["Resource Plans: Team Phases"])
class PlanPhaseViewSet(BaseViewSet):
    service_class = PlanPhaseService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_planphase",
            "create": "resource_plans.add_planphase",
            "partial_update": "resource_plans.change_planphase",
            "destroy": "resource_plans.delete_planphase",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List phases for a team assigned to a plan version project",
        responses={200: PlanPhaseSerializer(many=True)},
    )
    def list(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
        team_version_code: str | None = None,
    ):
        """GET .../teams/<team_version_code>/phases/"""
        phases = self.service.list_for_team(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
        )
        return self.response(
            data=PlanPhaseSerializer(phases, many=True).data,
            message="Phases retrieved successfully.",
        )

    @extend_schema(
        summary="Add a phase to a team assigned to a plan version project",
        request=PlanPhaseCreateSerializer,
        responses={
            201: PlanPhaseSerializer,
            404: OpenApiResponse(
                description="Plan, version, project, team, or sprint not found."
            ),
            409: OpenApiResponse(description="Phase name already used for this team."),
            422: OpenApiResponse(description="Validation failed."),
        },
    )
    def create(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
        team_version_code: str | None = None,
    ):
        """POST .../teams/<team_version_code>/phases/"""
        serializer = PlanPhaseCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanPhaseSerializer(obj).data,
            message="Phase added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a phase",
        request=PlanPhaseUpdateSerializer,
        responses={
            200: PlanPhaseSerializer,
            404: OpenApiResponse(description="Phase not found."),
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
        phase_version_code: str | None = None,
    ):
        """PATCH .../teams/<team_version_code>/phases/<phase_version_code>/"""
        serializer = PlanPhaseUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanPhaseSerializer(obj).data,
            message="Phase updated successfully.",
        )

    @extend_schema(
        summary="Remove a phase",
        responses={
            204: OpenApiResponse(description="Phase removed successfully."),
            404: OpenApiResponse(description="Phase not found."),
        },
    )
    def destroy(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
        team_version_code: str | None = None,
        phase_version_code: str | None = None,
    ):
        """DELETE .../teams/<team_version_code>/phases/<phase_version_code>/"""
        self.service.delete(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return self.response(
            message="Phase removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
