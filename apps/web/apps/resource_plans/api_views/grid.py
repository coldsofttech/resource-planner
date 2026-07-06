from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.exceptions import ValidationException
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.services import GridService

_TEAM_PARAM = OpenApiParameter(
    name="team",
    type=str,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "Team code to filter to a single team. Omit for all teams on the version."
    ),
)
_ALLOCATION_SET_PARAM = OpenApiParameter(
    name="allocation_set",
    type=str,
    location=OpenApiParameter.QUERY,
    required=True,
    description="AllocationSet code to read allocation data from.",
)


@extend_schema(tags=["Resource Plans: Allocation Grid"])
class GridViewSet(BaseViewSet):
    service_class = GridService

    def get_permissions(self):
        # All grid reads share the allocation set's view permission — there's
        # no dedicated model backing the "grid" itself.
        return [IsAuthenticated(), HasPermission("resource_plans.view_allocationset")]

    def _require_allocation_set_code(self, request: Request) -> str:
        allocation_set_code = request.query_params.get("allocation_set", "").strip()
        if not allocation_set_code:
            raise ValidationException(
                "The 'allocation_set' query parameter is required."
            )
        return allocation_set_code

    @extend_schema(
        summary="Per-member net capacity per sprint",
        parameters=[_TEAM_PARAM],
        responses={
            200: OpenApiResponse(
                description="Capacity totals per sprint + per-member breakdown."
            )
        },
    )
    def capacity(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/grid/capacity/"""
        result = self.service.capacity(
            plan_code=code,
            version=version,
            team_code=request.query_params.get("team") or None,
        )
        return self.response(data=result, message="Capacity retrieved successfully.")

    @extend_schema(
        summary=(
            "Per-sprint absence totals with holiday/leave/placeholder-leave breakdown"
        ),
        parameters=[_TEAM_PARAM],
        responses={
            200: OpenApiResponse(description="Absence totals + type breakdown.")
        },
    )
    def absences(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/grid/absences/"""
        result = self.service.absences(
            plan_code=code,
            version=version,
            team_code=request.query_params.get("team") or None,
        )
        return self.response(data=result, message="Absences retrieved successfully.")

    @extend_schema(
        summary="Per-member allocated days vs net capacity per sprint",
        parameters=[_TEAM_PARAM, _ALLOCATION_SET_PARAM],
        responses={
            200: OpenApiResponse(
                description="Allocated-vs-capacity per member per sprint."
            ),
            404: OpenApiResponse(description="Allocation set not found."),
            422: OpenApiResponse(
                description="The 'allocation_set' query parameter is required."
            ),
        },
    )
    def allocated_capacity(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/grid/allocated-capacity/"""
        result = self.service.allocated_capacity(
            plan_code=code,
            version=version,
            allocation_set_code=self._require_allocation_set_code(request),
            team_code=request.query_params.get("team") or None,
        )
        return self.response(
            data=result, message="Allocated capacity retrieved successfully."
        )

    @extend_schema(
        summary=(
            "Days allocated per engineer per sprint by programme, project, and phase"
        ),
        parameters=[_TEAM_PARAM, _ALLOCATION_SET_PARAM],
        responses={
            200: OpenApiResponse(
                description=("Allocation rows grouped by member/team/project/phase.")
            ),
            404: OpenApiResponse(description="Allocation set not found."),
            422: OpenApiResponse(
                description="The 'allocation_set' query parameter is required."
            ),
        },
    )
    def allocations(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/grid/allocations/"""
        result = self.service.allocations(
            plan_code=code,
            version=version,
            allocation_set_code=self._require_allocation_set_code(request),
            team_code=request.query_params.get("team") or None,
        )
        return self.response(data=result, message="Allocations retrieved successfully.")
