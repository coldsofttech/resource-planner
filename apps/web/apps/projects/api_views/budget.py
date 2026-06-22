from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin
from apps.projects.serializers import (
    ProjectBudgetCreateSerializer,
    ProjectBudgetDetailSerializer,
    ProjectBudgetLifetimeSerializer,
    ProjectBudgetListSerializer,
    ProjectBudgetStatusHistorySerializer,
    ProjectBudgetUpdateSerializer,
)
from apps.projects.services import ProjectBudgetExportService, ProjectBudgetService


@extend_schema(tags=["Projects: Budgets"])
class ProjectBudgetViewSet(ExportMixin, BaseViewSet):
    service_class = ProjectBudgetService
    export_service_class = ProjectBudgetExportService

    export_columns = [
        {"key": "code", "label": "Code", "default": True},
        {"key": "project", "label": "Project", "default": True},
        {"key": "financial_year", "label": "Financial Year", "default": True},
        {"key": "allocated_budget", "label": "Allocated Budget (£)", "default": True},
        {"key": "refined_budget", "label": "Refined Budget (£)", "default": True},
        {"key": "actual_budget", "label": "Actual Budget (£)", "default": True},
        {"key": "estimate_version", "label": "Estimate Version", "default": True},
        {"key": "remaining_budget", "label": "Remaining Budget (£)", "default": True},
        {"key": "note", "label": "Note", "default": False},
        {"key": "created_at", "label": "Created On", "default": False},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectbudget",
            "retrieve": "projects.view_projectbudget",
            "create": "projects.add_projectbudget",
            "partial_update": "projects.change_projectbudget",
            "destroy": "projects.delete_projectbudget",
            "history": "projects.view_projectbudget",
            "lifetime": "projects.view_projectbudget",
            "export_specs": "projects.export_projectbudget",
            "export": "projects.export_projectbudget",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List budgets for a project",
        responses={200: ProjectBudgetListSerializer(many=True)},
    )
    def list(self, request: Request, code=None):
        """GET /projects/<code>/budgets/"""
        params = self.get_list_params(request)
        result = self.service.list(project_code=code, params=params)
        return self.paginated_response(
            result=result,
            serializer_class=ProjectBudgetListSerializer,
            message="Budgets retrieved successfully.",
        )

    @extend_schema(
        summary="Retrieve a project budget",
        responses={
            200: ProjectBudgetDetailSerializer,
            404: OpenApiResponse(description="Budget not found."),
        },
    )
    def retrieve(self, request: Request, code=None, budget_code=None):
        """GET /projects/<code>/budgets/<budget_code>/"""
        obj = self.service.get(code=budget_code)
        return self.response(
            data=ProjectBudgetDetailSerializer(
                obj, context=self.get_serializer_context()
            ).data
        )

    @extend_schema(
        summary="Create a project budget",
        request=ProjectBudgetCreateSerializer,
        responses={
            201: ProjectBudgetDetailSerializer,
            400: OpenApiResponse(description="Validation error."),
            409: OpenApiResponse(
                description="Budget already exists for this project and financial year."
            ),
        },
    )
    def create(self, request: Request, code=None):
        """POST /projects/<code>/budgets/"""
        serializer = ProjectBudgetCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(project_code=code, **serializer.validated_data)
        return self.response(
            data=ProjectBudgetDetailSerializer(
                obj, context=self.get_serializer_context()
            ).data,
            message="Budget created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a project budget",
        request=ProjectBudgetUpdateSerializer,
        responses={
            200: ProjectBudgetDetailSerializer,
            404: OpenApiResponse(description="Budget not found."),
        },
    )
    def partial_update(self, request: Request, code=None, budget_code=None):
        """PATCH /projects/<code>/budgets/<budget_code>/"""
        serializer = ProjectBudgetUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=budget_code, **serializer.validated_data)
        return self.response(
            data=ProjectBudgetDetailSerializer(
                obj, context=self.get_serializer_context()
            ).data,
            message="Budget updated successfully.",
        )

    @extend_schema(
        summary="Delete a project budget",
        responses={
            204: OpenApiResponse(description="Budget deleted."),
            404: OpenApiResponse(description="Budget not found."),
        },
    )
    def destroy(self, request: Request, code=None, budget_code=None):
        """DELETE /projects/<code>/budgets/<budget_code>/"""
        self.service.delete(code=budget_code)
        return self.response(
            message="Budget deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="List status history for a project budget",
        responses={200: ProjectBudgetStatusHistorySerializer(many=True)},
    )
    def history(self, request: Request, code=None, budget_code=None):
        """GET /projects/<code>/budgets/<budget_code>/history/"""
        rows = self.service.history(code=budget_code)
        data = ProjectBudgetStatusHistorySerializer(rows, many=True).data
        return self.response(data=data, message="History retrieved successfully.")

    @extend_schema(
        summary="Get lifetime budget summary for a project",
        responses={200: ProjectBudgetLifetimeSerializer},
    )
    def lifetime(self, request: Request, code=None):
        """GET /projects/<code>/budgets/lifetime/"""
        data = self.service.lifetime(project_code=code)
        return self.response(
            data=ProjectBudgetLifetimeSerializer(data).data,
            message="Lifetime budget summary retrieved successfully.",
        )
