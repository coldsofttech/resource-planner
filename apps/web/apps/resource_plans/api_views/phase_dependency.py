from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    AvailablePredecessorPhaseSerializer,
    PlanPhaseDependencyCreateSerializer,
    PlanPhaseDependencySerializer,
    PlanPhaseDependencyUpdateSerializer,
)
from apps.resource_plans.services import PlanPhaseDependencyService


@extend_schema(tags=["Resource Plans: Phase Dependencies"])
class PlanPhaseDependencyViewSet(BaseViewSet):
    service_class = PlanPhaseDependencyService

    def get_permissions(self):
        action_perms = {
            "available_predecessors": "resource_plans.view_planphasedependency",
            "list": "resource_plans.view_planphasedependency",
            "create": "resource_plans.add_planphasedependency",
            "partial_update": "resource_plans.change_planphasedependency",
            "destroy": "resource_plans.delete_planphasedependency",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List phases available as a predecessor for a phase",
        responses={200: AvailablePredecessorPhaseSerializer(many=True)},
    )
    def available_predecessors(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
        team_version_code: str | None = None,
        phase_version_code: str | None = None,
    ):
        """GET .../phases/<phase_version_code>/dependencies/available-predecessors/"""
        phases = self.service.list_available_predecessors(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return self.response(
            data=AvailablePredecessorPhaseSerializer(phases, many=True).data,
            message="Available predecessor phases retrieved successfully.",
        )

    @extend_schema(
        summary="List dependencies for a phase",
        responses={200: PlanPhaseDependencySerializer(many=True)},
    )
    def list(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        project_version_code: str | None = None,
        team_version_code: str | None = None,
        phase_version_code: str | None = None,
    ):
        """GET .../phases/<phase_version_code>/dependencies/"""
        dependencies = self.service.list_for_phase(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return self.response(
            data=PlanPhaseDependencySerializer(dependencies, many=True).data,
            message="Dependencies retrieved successfully.",
        )

    @extend_schema(
        summary="Add a dependency to a phase",
        request=PlanPhaseDependencyCreateSerializer,
        responses={
            201: PlanPhaseDependencySerializer,
            404: OpenApiResponse(
                description=(
                    "Plan, version, project, team, phase, or predecessor not found."
                )
            ),
            409: OpenApiResponse(description="Dependency already exists."),
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
        phase_version_code: str | None = None,
    ):
        """POST .../phases/<phase_version_code>/dependencies/"""
        serializer = PlanPhaseDependencyCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanPhaseDependencySerializer(obj).data,
            message="Dependency added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a dependency",
        request=PlanPhaseDependencyUpdateSerializer,
        responses={
            200: PlanPhaseDependencySerializer,
            404: OpenApiResponse(description="Dependency or predecessor not found."),
            409: OpenApiResponse(description="Dependency already exists."),
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
        dependency_version_code: str | None = None,
    ):
        """PATCH .../phases/<phase_version_code>/dependencies/<dep_version_code>/"""
        serializer = PlanPhaseDependencyUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            dependency_version_code=dependency_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanPhaseDependencySerializer(obj).data,
            message="Dependency updated successfully.",
        )

    @extend_schema(
        summary="Remove a dependency",
        responses={
            204: OpenApiResponse(description="Dependency removed successfully."),
            404: OpenApiResponse(description="Dependency not found."),
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
        dependency_version_code: str | None = None,
    ):
        """DELETE .../phases/<phase_version_code>/dependencies/<dep_version_code>/"""
        self.service.delete(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            dependency_version_code=dependency_version_code,
        )
        return self.response(
            message="Dependency removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
