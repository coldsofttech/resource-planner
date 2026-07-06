from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.projects.services.burn_tracker import BurnTrackerService


@extend_schema(tags=["Projects: Burn Tracker"])
class BurnTrackerViewSet(BaseViewSet):
    service_class = BurnTrackerService

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_project",
            "mark_done": "projects.change_project",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(summary="List burn tracker rows for a financial year")
    def list(self, request: Request):
        """GET /projects/burn-tracker/?fy=&search=&programme=&team=&status=&risk="""
        params = self.get_list_params(request)
        fy_code = request.query_params.get("fy") or ""
        sort_param = params.sorts[0] if params.sorts else None
        data = self.service.list_data(
            fy_code=fy_code,
            search=request.query_params.get("search") or None,
            programme_code=request.query_params.get("programme") or None,
            team_code=request.query_params.get("team") or None,
            status_code=request.query_params.get("status") or None,
            risk_filter=request.query_params.get("risk") or None,
            sort=sort_param.sort_by if sort_param else None,
            order_by="DESC"
            if (sort_param and sort_param.direction == "desc")
            else "ASC",
            page=params.page,
            page_size=params.page_size,
        )
        return self.response(data=data, message="Burn tracker data retrieved.")

    @extend_schema(summary="Mark a project as done in the burn tracker")
    def mark_done(self, request: Request, code: str | None = None):
        """POST /projects/burn-tracker/<code>/done/"""
        sprint_code = request.data.get("sprint_code") or ""
        data = self.service.mark_done(project_code=code, sprint_code=sprint_code)
        return self.response(data=data, message="Project marked as done.")
