from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    PlanPhasePauseCreateSerializer,
    PlanPhasePauseSerializer,
    PlanPhasePauseUpdateSerializer,
)
from apps.resource_plans.services import PlanPhasePauseService


@extend_schema(tags=["Resource Plans: Phase Pauses"])
class PlanPhasePauseViewSet(BaseViewSet):
    service_class = PlanPhasePauseService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_planphasepause",
            "create": "resource_plans.add_planphasepause",
            "partial_update": "resource_plans.change_planphasepause",
            "destroy": "resource_plans.delete_planphasepause",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List pauses for a phase",
        responses={200: PlanPhasePauseSerializer(many=True)},
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
        """GET .../phases/<phase_version_code>/pauses/"""
        pauses = self.service.list_for_phase(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return self.response(
            data=PlanPhasePauseSerializer(pauses, many=True).data,
            message="Pauses retrieved successfully.",
        )

    @extend_schema(
        summary="Add a pause to a phase",
        request=PlanPhasePauseCreateSerializer,
        responses={
            201: PlanPhasePauseSerializer,
            404: OpenApiResponse(
                description="Plan, version, project, team, phase, or sprint not found."
            ),
            409: OpenApiResponse(description="A pause already exists at this sprint."),
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
        """POST .../phases/<phase_version_code>/pauses/"""
        serializer = PlanPhasePauseCreateSerializer(
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
            data=PlanPhasePauseSerializer(obj).data,
            message="Pause added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a pause",
        request=PlanPhasePauseUpdateSerializer,
        responses={
            200: PlanPhasePauseSerializer,
            404: OpenApiResponse(description="Pause or sprint not found."),
            409: OpenApiResponse(description="A pause already exists at this sprint."),
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
        pause_version_code: str | None = None,
    ):
        """PATCH .../phases/<phase_version_code>/pauses/<pause_version_code>/"""
        serializer = PlanPhasePauseUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            pause_version_code=pause_version_code,
            **serializer.validated_data,
        )
        return self.response(
            data=PlanPhasePauseSerializer(obj).data,
            message="Pause updated successfully.",
        )

    @extend_schema(
        summary="Remove a pause",
        responses={
            204: OpenApiResponse(description="Pause removed successfully."),
            404: OpenApiResponse(description="Pause not found."),
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
        pause_version_code: str | None = None,
    ):
        """DELETE .../phases/<phase_version_code>/pauses/<pause_version_code>/"""
        self.service.delete(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            pause_version_code=pause_version_code,
        )
        return self.response(
            message="Pause removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
