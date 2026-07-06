from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    PlanPhaseSegmentCreateSerializer,
    PlanPhaseSegmentSerializer,
)
from apps.resource_plans.services import PlanPhaseSegmentService


@extend_schema(tags=["Resource Plans: Phase Segments"])
class PlanPhaseSegmentViewSet(BaseViewSet):
    service_class = PlanPhaseSegmentService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_planphasesegment",
            "create": "resource_plans.add_planphasesegment",
            "destroy": "resource_plans.delete_planphasesegment",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List segments for a phase",
        responses={200: PlanPhaseSegmentSerializer(many=True)},
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
        """GET .../phases/<phase_version_code>/segments/"""
        segments = self.service.list_for_phase(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
        )
        return self.response(
            data=PlanPhaseSegmentSerializer(segments, many=True).data,
            message="Segments retrieved successfully.",
        )

    @extend_schema(
        summary="Add a segment to a phase",
        request=PlanPhaseSegmentCreateSerializer,
        responses={
            201: PlanPhaseSegmentSerializer,
            404: OpenApiResponse(
                description="Plan, version, project, team, or phase not found."
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
        """POST .../phases/<phase_version_code>/segments/"""
        serializer = PlanPhaseSegmentCreateSerializer(
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
            data=PlanPhaseSegmentSerializer(obj).data,
            message="Segment added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Remove a segment",
        responses={
            204: OpenApiResponse(description="Segment removed successfully."),
            404: OpenApiResponse(description="Segment not found."),
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
        segment_version_code: str | None = None,
    ):
        """DELETE .../phases/<phase_version_code>/segments/<segment_version_code>/"""
        self.service.delete(
            plan_code=code,
            version=version,
            project_version_code=project_version_code,
            team_version_code=team_version_code,
            phase_version_code=phase_version_code,
            segment_version_code=segment_version_code,
        )
        return self.response(
            message="Segment removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
