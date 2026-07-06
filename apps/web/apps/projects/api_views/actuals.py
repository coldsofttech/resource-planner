from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers import ProjectActualConfigSerializer
from apps.projects.services.project_actuals import ProjectActualsService


@extend_schema(tags=["Projects: Actuals"])
class ProjectActualsViewSet(BaseViewSet):
    service_class = ProjectActualsService

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_project",
            "summary": "projects.view_project",
            "get_config": "projects.view_project",
            "update_config": "projects.change_project",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(summary="Get actuals table data for a project")
    def list(self, request: Request, code: str | None = None):
        """GET /projects/<code>/actuals/?fy=<fy_code>"""
        fy_code = request.query_params.get("fy") or None
        rows = self.service.table_data(project_code=code, fy_code=fy_code)
        return self.response(data={"results": rows}, message="Actuals retrieved.")

    @extend_schema(summary="Get actuals summary cards for a project")
    def summary(self, request: Request, code: str | None = None):
        """GET /projects/<code>/actuals/summary/"""
        data = self.service.summary(project_code=code)
        return self.response(data=data, message="Actuals summary retrieved.")

    @extend_schema(summary="Get actuals configuration for a project")
    def get_config(self, request: Request, code: str | None = None):
        """GET /projects/<code>/actuals/config/"""
        data = self.service.get_config(project_code=code)
        return self.response(data=data, message="Actuals config retrieved.")

    @extend_schema(summary="Update actuals configuration for a project")
    def update_config(self, request: Request, code: str | None = None):
        """PATCH /projects/<code>/actuals/config/"""
        serializer = ProjectActualConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = self.service.update_config(
            project_code=code, **serializer.validated_data
        )
        return self.response(data=data, message="Actuals config updated.")
