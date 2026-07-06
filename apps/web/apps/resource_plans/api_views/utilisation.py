from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.exceptions import ValidationException
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.services import UtilisationService

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
_INCLUDE_PLACEHOLDERS_PARAM = OpenApiParameter(
    name="include_placeholders",
    type=bool,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "Include auto-generated engineer placeholder allocations in team totals."
    ),
)
_MEMBER_PARAM = OpenApiParameter(
    name="member",
    type=str,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Member code to filter to a single member.",
)
_EMPLOYMENT_TYPE_PARAM = OpenApiParameter(
    name="employment_type",
    type=str,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Employment type code to filter members by.",
)
_PROJECT_PARAM = OpenApiParameter(
    name="project",
    type=str,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Project code to scope the allocated-days figure to.",
)
_PROGRAMME_PARAM = OpenApiParameter(
    name="programme",
    type=str,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "Programme code to filter to a single programme. Omit for all "
        "programmes on the version."
    ),
)


@extend_schema(tags=["Resource Plans: Utilisation"])
class UtilisationViewSet(BaseViewSet):
    service_class = UtilisationService

    def get_permissions(self):
        # Read-only aggregation over existing permission-gated data — no
        # dedicated model backs "utilisation" itself.
        return [IsAuthenticated(), HasPermission("resource_plans.view_allocationset")]

    def _require_allocation_set_code(self, request: Request) -> str:
        allocation_set_code = request.query_params.get("allocation_set", "").strip()
        if not allocation_set_code:
            raise ValidationException(
                "The 'allocation_set' query parameter is required."
            )
        return allocation_set_code

    @extend_schema(
        summary="Per-team net capacity, allocated days, and utilisation % per sprint",
        parameters=[_TEAM_PARAM, _ALLOCATION_SET_PARAM, _INCLUDE_PLACEHOLDERS_PARAM],
        responses={
            200: OpenApiResponse(
                description="Aggregate chart series + per-team summary rows."
            ),
            404: OpenApiResponse(description="Allocation set not found."),
            422: OpenApiResponse(
                description="The 'allocation_set' query parameter is required."
            ),
        },
    )
    def teams(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/utilisation/teams/"""
        include_placeholders = request.query_params.get(
            "include_placeholders", ""
        ).lower() in ("true", "1")
        result = self.service.teams(
            plan_code=code,
            version=version,
            allocation_set_code=self._require_allocation_set_code(request),
            team_code=request.query_params.get("team") or None,
            include_placeholders=include_placeholders,
        )
        return self.response(
            data=result, message="Team utilisation retrieved successfully."
        )

    @extend_schema(
        summary="Per-member net capacity, allocated days, and utilisation % per sprint",
        parameters=[
            _TEAM_PARAM,
            _ALLOCATION_SET_PARAM,
            _MEMBER_PARAM,
            _EMPLOYMENT_TYPE_PARAM,
            _PROJECT_PARAM,
        ],
        responses={
            200: OpenApiResponse(
                description="Aggregate chart series + per-member summary rows."
            ),
            404: OpenApiResponse(
                description=(
                    "Allocation set, member, employment type, or project not found."
                )
            ),
            422: OpenApiResponse(
                description="The 'allocation_set' query parameter is required."
            ),
        },
    )
    def members(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/utilisation/members/"""
        result = self.service.members(
            plan_code=code,
            version=version,
            allocation_set_code=self._require_allocation_set_code(request),
            team_code=request.query_params.get("team") or None,
            member_code=request.query_params.get("member") or None,
            employment_type_code=request.query_params.get("employment_type") or None,
            project_code=request.query_params.get("project") or None,
        )
        return self.response(
            data=result, message="Member utilisation retrieved successfully."
        )

    @extend_schema(
        summary=(
            "Per-programme budget baseline, forecast cost, and cumulative "
            "cost per sprint"
        ),
        parameters=[_PROGRAMME_PARAM],
        responses={
            200: OpenApiResponse(
                description="Per-programme chart series + Budget/Forecast totals."
            ),
            404: OpenApiResponse(description="Programme not found on this version."),
        },
    )
    def programmes(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/utilisation/programmes/"""
        result = self.service.programmes(
            plan_code=code,
            version=version,
            programme_code=request.query_params.get("programme") or None,
        )
        return self.response(
            data=result, message="Programme utilisation retrieved successfully."
        )
