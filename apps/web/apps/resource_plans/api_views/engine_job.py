from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    EngineJobCreateSerializer,
    EngineJobSerializer,
)
from apps.resource_plans.services import EngineJobService


@extend_schema(tags=["Resource Plans: Engine Jobs"])
class EngineJobViewSet(BaseViewSet):
    service_class = EngineJobService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_enginejob",
            "retrieve": "resource_plans.view_enginejob",
            "create": "resource_plans.add_enginejob",
            "destroy": "resource_plans.delete_enginejob",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List engine jobs for a plan (plan-wide history)",
        responses={200: EngineJobSerializer(many=True)},
    )
    def list(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
    ):
        """GET .../versions/<version>/engine-jobs/"""
        mode = request.query_params.get("mode") or None
        jobs = self.service.list_for_plan(plan_code=code, version=version, mode=mode)
        return self.response(
            data=EngineJobSerializer(jobs, many=True).data,
            message="Engine jobs retrieved successfully.",
        )

    @extend_schema(
        summary="Run the engine (create an engine job)",
        request=EngineJobCreateSerializer,
        responses={
            201: EngineJobSerializer,
            404: OpenApiResponse(description="Plan or version not found."),
            422: OpenApiResponse(description="Validation failed."),
        },
    )
    def create(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
    ):
        """POST .../versions/<version>/engine-jobs/"""
        serializer = EngineJobCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(
            plan_code=code, version=version, **serializer.validated_data
        )
        return self.response(
            data=EngineJobSerializer(obj).data,
            message="Engine job started successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Retrieve an engine job (used for polling progress)",
        responses={
            200: EngineJobSerializer,
            404: OpenApiResponse(description="Engine job not found."),
        },
    )
    def retrieve(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        job_code: str | None = None,
    ):
        """GET .../engine-jobs/<job_code>/"""
        obj = self.service.get(plan_code=code, version=version, job_code=job_code)
        return self.response(
            data=EngineJobSerializer(obj).data,
            message="Engine job retrieved successfully.",
        )

    @extend_schema(
        summary="Delete an engine job history entry",
        responses={
            204: OpenApiResponse(description="Engine job removed successfully."),
            404: OpenApiResponse(description="Engine job not found."),
        },
    )
    def destroy(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        job_code: str | None = None,
    ):
        """DELETE .../engine-jobs/<job_code>/"""
        self.service.delete(plan_code=code, version=version, job_code=job_code)
        return self.response(
            message="Engine job removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
