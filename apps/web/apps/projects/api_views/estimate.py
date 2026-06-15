from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin
from apps.projects.serializers import (
    ProjectEstimateCreateSerializer,
    ProjectEstimateDetailSerializer,
    ProjectEstimateListSerializer,
    ProjectEstimateStatusHistorySerializer,
    ProjectEstimateUpdateSerializer,
)
from apps.projects.services import ProjectEstimateExportService, ProjectEstimateService


@extend_schema(tags=["Projects: Estimates"])
class ProjectEstimateViewSet(ExportMixin, BaseViewSet):
    service_class = ProjectEstimateService
    export_service_class = ProjectEstimateExportService

    export_columns = [
        {"key": "code", "label": "Code", "default": True},
        {"key": "project", "label": "Project", "default": True},
        {"key": "version", "label": "Version", "default": True},
        {"key": "status", "label": "Status", "default": True},
        {"key": "estimate_days", "label": "Estimate Days", "default": True},
        {"key": "contingency_percentage", "label": "Contingency %", "default": True},
        {"key": "day_rate", "label": "Day Rate (£)", "default": True},
        {"key": "total_cost", "label": "Total Cost (£)", "default": True},
        {"key": "estimate_link", "label": "Estimate Link", "default": False},
        {
            "key": "approval_email_sent",
            "label": "Approval Email Sent",
            "default": False,
        },
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": False},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectestimate",
            "retrieve": "projects.view_projectestimate",
            "create": "projects.add_projectestimate",
            "partial_update": "projects.change_projectestimate",
            "destroy": "projects.delete_projectestimate",
            "activate": "projects.change_projectestimate",
            "deactivate": "projects.change_projectestimate",
            "history": "projects.view_projectestimate",
            "export_specs": "projects.export_projectestimate",
            "export": "projects.export_projectestimate",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List estimates for a project",
        responses={200: ProjectEstimateListSerializer(many=True)},
    )
    def list(self, request: Request, code=None):
        """GET /projects/<code>/estimates/"""
        params = self.get_list_params(request)
        result = self.service.list(project_code=code, params=params)
        return self.paginated_response(
            result=result,
            serializer_class=ProjectEstimateListSerializer,
            message="Estimates retrieved successfully.",
        )

    @extend_schema(
        summary="Retrieve a project estimate",
        responses={
            200: ProjectEstimateDetailSerializer,
            404: OpenApiResponse(description="Estimate not found."),
        },
    )
    def retrieve(self, request: Request, code=None, estimate_code=None):
        """GET /projects/<code>/estimates/<estimate_code>/"""
        obj = self.service.get(code=estimate_code)
        return self.response(
            data=ProjectEstimateDetailSerializer(
                obj, context=self.get_serializer_context()
            ).data
        )

    @extend_schema(
        summary="Create a project estimate",
        request=ProjectEstimateCreateSerializer,
        responses={
            201: ProjectEstimateDetailSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def create(self, request: Request, code=None):
        """POST /projects/<code>/estimates/"""
        serializer = ProjectEstimateCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(project_code=code, **serializer.validated_data)
        return self.response(
            data=ProjectEstimateDetailSerializer(
                obj, context=self.get_serializer_context()
            ).data,
            message="Estimate created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a project estimate",
        request=ProjectEstimateUpdateSerializer,
        responses={
            200: ProjectEstimateDetailSerializer,
            404: OpenApiResponse(description="Estimate not found."),
        },
    )
    def partial_update(self, request: Request, code=None, estimate_code=None):
        """PATCH /projects/<code>/estimates/<estimate_code>/"""
        serializer = ProjectEstimateUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=estimate_code, **serializer.validated_data)
        return self.response(
            data=ProjectEstimateDetailSerializer(
                obj, context=self.get_serializer_context()
            ).data,
            message="Estimate updated successfully.",
        )

    @extend_schema(
        summary="Delete a project estimate",
        responses={
            204: OpenApiResponse(description="Estimate deleted."),
            404: OpenApiResponse(description="Estimate not found."),
        },
    )
    def destroy(self, request: Request, code=None, estimate_code=None):
        """DELETE /projects/<code>/estimates/<estimate_code>/"""
        self.service.delete(code=estimate_code)
        return self.response(
            message="Estimate deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Activate a project estimate",
        responses={200: ProjectEstimateDetailSerializer},
    )
    def activate(self, request: Request, code=None, estimate_code=None):
        """POST /projects/<code>/estimates/<estimate_code>/activate/"""
        obj = self.service.activate(code=estimate_code)
        return self.response(
            data=ProjectEstimateDetailSerializer(
                obj, context=self.get_serializer_context()
            ).data,
            message="Estimate activated.",
        )

    @extend_schema(
        summary="Deactivate a project estimate",
        responses={200: ProjectEstimateDetailSerializer},
    )
    def deactivate(self, request: Request, code=None, estimate_code=None):
        """POST /projects/<code>/estimates/<estimate_code>/deactivate/"""
        obj = self.service.deactivate(code=estimate_code)
        return self.response(
            data=ProjectEstimateDetailSerializer(
                obj, context=self.get_serializer_context()
            ).data,
            message="Estimate deactivated.",
        )

    @extend_schema(
        summary="List status history for a project estimate",
        responses={200: ProjectEstimateStatusHistorySerializer(many=True)},
    )
    def history(self, request: Request, code=None, estimate_code=None):
        """GET /projects/<code>/estimates/<estimate_code>/history/"""
        rows = self.service.history(code=estimate_code)
        data = ProjectEstimateStatusHistorySerializer(rows, many=True).data
        return self.response(data=data, message="History retrieved successfully.")
