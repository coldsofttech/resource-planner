from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.exceptions import ValidationException
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    SnapshotAllocationSerializer,
    SnapshotCreateSerializer,
    SnapshotSerializer,
)
from apps.resource_plans.services import SnapshotService

_SPRINT_PARAM = OpenApiParameter(
    name="sprint", type=int, location=OpenApiParameter.QUERY, required=False
)
_MEMBER_PARAM = OpenApiParameter(
    name="member", type=str, location=OpenApiParameter.QUERY, required=False
)
_TEAM_PARAM = OpenApiParameter(
    name="team", type=str, location=OpenApiParameter.QUERY, required=False
)
_PROJECT_PARAM = OpenApiParameter(
    name="project", type=str, location=OpenApiParameter.QUERY, required=False
)
_TYPE_PARAM = OpenApiParameter(
    name="type", type=str, location=OpenApiParameter.QUERY, required=False
)
_SNAPSHOT_A_PARAM = OpenApiParameter(
    name="a", type=str, location=OpenApiParameter.QUERY, required=True
)
_SNAPSHOT_B_PARAM = OpenApiParameter(
    name="b", type=str, location=OpenApiParameter.QUERY, required=True
)


@extend_schema(tags=["Resource Plans: Snapshots"])
class SnapshotViewSet(BaseViewSet):
    service_class = SnapshotService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_snapshot",
            "retrieve": "resource_plans.view_snapshot",
            "create": "resource_plans.add_snapshot",
            "destroy": "resource_plans.delete_snapshot",
            "allocations": "resource_plans.view_snapshot",
            "allocation_filter_options": "resource_plans.view_snapshot",
            "compare": "resource_plans.view_snapshot",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List snapshots for a resource plan version",
        responses={200: SnapshotSerializer(many=True)},
    )
    def list(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/snapshots/"""
        params = self.get_list_params(request)
        result = self.service.list_for_version(
            plan_code=code, version=version, params=params
        )
        return self.paginated_response(
            result=result,
            serializer_class=SnapshotSerializer,
            message="Snapshots retrieved successfully.",
        )

    @extend_schema(
        summary="Take a snapshot of a resource plan version",
        request=SnapshotCreateSerializer,
        responses={201: SnapshotSerializer},
    )
    def create(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """POST .../versions/<version>/snapshots/"""
        serializer = SnapshotCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(
            plan_code=code, version=version, **serializer.validated_data
        )
        return self.response(
            data=SnapshotSerializer(obj).data,
            message="Snapshot started successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Retrieve a snapshot (also used for status polling)",
        responses={
            200: SnapshotSerializer,
            404: OpenApiResponse(description="Snapshot not found."),
        },
    )
    def retrieve(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        snapshot_code: str | None = None,
    ):
        """GET .../snapshots/<snapshot_code>/"""
        obj = self.service.get(
            plan_code=code, version=version, snapshot_code=snapshot_code
        )
        return self.response(
            data=SnapshotSerializer(obj).data,
            message="Snapshot retrieved successfully.",
        )

    @extend_schema(
        summary="Delete a snapshot",
        responses={
            204: OpenApiResponse(description="Snapshot removed successfully."),
            404: OpenApiResponse(description="Snapshot not found."),
        },
    )
    def destroy(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        snapshot_code: str | None = None,
    ):
        """DELETE .../snapshots/<snapshot_code>/"""
        self.service.delete(
            plan_code=code, version=version, snapshot_code=snapshot_code
        )
        return self.response(
            message="Snapshot removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="List a snapshot's denormalized allocation rows",
        parameters=[
            _SPRINT_PARAM,
            _MEMBER_PARAM,
            _TEAM_PARAM,
            _PROJECT_PARAM,
            _TYPE_PARAM,
        ],
        responses={200: SnapshotAllocationSerializer(many=True)},
    )
    def allocations(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        snapshot_code: str | None = None,
    ):
        """GET .../snapshots/<snapshot_code>/allocations/"""
        params = self.get_list_params(request)
        result = self.service.list_allocations(
            plan_code=code,
            version=version,
            snapshot_code=snapshot_code,
            params=params,
        )
        return self.paginated_response(
            result=result,
            serializer_class=SnapshotAllocationSerializer,
            message="Snapshot allocations retrieved successfully.",
        )

    @extend_schema(
        summary="Distinct filter values available for a snapshot's allocations",
        responses={
            200: OpenApiResponse(
                description="Distinct sprint/member/team/project/type values."
            )
        },
    )
    def allocation_filter_options(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        snapshot_code: str | None = None,
    ):
        """GET .../snapshots/<snapshot_code>/allocations/filter-options/"""
        result = self.service.get_allocation_filter_options(
            plan_code=code, version=version, snapshot_code=snapshot_code
        )
        return self.response(
            data=result, message="Filter options retrieved successfully."
        )

    @extend_schema(
        summary="Compare two snapshots — git-like diff of allocation rows",
        parameters=[_SNAPSHOT_A_PARAM, _SNAPSHOT_B_PARAM],
        responses={
            200: OpenApiResponse(description="Diff rows between snapshot A and B."),
            404: OpenApiResponse(description="One or both snapshots not found."),
            422: OpenApiResponse(
                description="Both 'a' and 'b' query parameters are required."
            ),
        },
    )
    def compare(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/snapshots/compare/?a=<code>&b=<code>"""
        snapshot_a_code = request.query_params.get("a", "").strip()
        snapshot_b_code = request.query_params.get("b", "").strip()
        if not snapshot_a_code or not snapshot_b_code:
            raise ValidationException("Both 'a' and 'b' query parameters are required.")
        result = self.service.compare(
            plan_code=code,
            version=version,
            snapshot_a_code=snapshot_a_code,
            snapshot_b_code=snapshot_b_code,
        )
        return self.response(data=result, message="Snapshots compared successfully.")
