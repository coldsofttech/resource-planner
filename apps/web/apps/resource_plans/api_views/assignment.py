from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    PlanAssignmentCreateSerializer,
    PlanAssignmentSerializer,
    PlanAssignmentUpdateSerializer,
)
from apps.resource_plans.services import PlanAssignmentService


@extend_schema(tags=["Resource Plans: Assignments"])
class PlanAssignmentViewSet(BaseViewSet):
    service_class = PlanAssignmentService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_planassignment",
            "create": "resource_plans.add_planassignment",
            "partial_update": "resource_plans.change_planassignment",
            "destroy": "resource_plans.delete_planassignment",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List assignments for a phase",
        responses={200: PlanAssignmentSerializer(many=True)},
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
        """GET .../phases/<phase_version_code>/assignments/"""
        assignments = self.service.list_for_phase(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return self.response(
            data=PlanAssignmentSerializer(assignments, many=True).data,
            message="Assignments retrieved successfully.",
        )

    @extend_schema(
        summary="Add an assignment to a phase",
        request=PlanAssignmentCreateSerializer,
        responses={
            201: PlanAssignmentSerializer,
            404: OpenApiResponse(
                description="Plan, version, project, team, phase, or member not found."
            ),
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
        """POST .../phases/<phase_version_code>/assignments/"""
        serializer = PlanAssignmentCreateSerializer(
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
            data=PlanAssignmentSerializer(obj).data,
            message="Assignment added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update an assignment",
        request=PlanAssignmentUpdateSerializer,
        responses={
            200: PlanAssignmentSerializer,
            404: OpenApiResponse(description="Assignment or member not found."),
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
        assignment_version_code: str | None = None,
    ):
        """PATCH .../phases/<phase_version_code>/assignments/<assign_version_code>/"""
        serializer = PlanAssignmentUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            assignment_version_code=assignment_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanAssignmentSerializer(obj).data,
            message="Assignment updated successfully.",
        )

    @extend_schema(
        summary="Remove an assignment",
        responses={
            204: OpenApiResponse(description="Assignment removed successfully."),
            404: OpenApiResponse(description="Assignment not found."),
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
        assignment_version_code: str | None = None,
    ):
        """DELETE .../phases/<phase_version_code>/assignments/<assign_version_code>/"""
        self.service.delete(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            assignment_version_code=assignment_version_code,
        )
        return self.response(
            message="Assignment removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
