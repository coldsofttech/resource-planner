from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    AllocationOverrideSerializer,
    AllocationSerializer,
)
from apps.resource_plans.services import AllocationService


@extend_schema(tags=["Resource Plans: Allocations"])
class AllocationViewSet(BaseViewSet):
    service_class = AllocationService

    def get_permissions(self):
        action_perms = {
            "override": "resource_plans.change_allocation",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Set or clear an allocation's override days",
        description=(
            "Only permitted while the allocation set is Draft. Automatically "
            "refreshes THRESHOLD_BREACH conflicts for the allocation set "
            "after the edit."
        ),
        request=AllocationOverrideSerializer,
        responses={
            200: AllocationSerializer,
            404: OpenApiResponse(description="Allocation set or allocation not found."),
            422: OpenApiResponse(
                description=(
                    "Only allocations in a draft allocation set can be overridden."
                )
            ),
        },
    )
    def override(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
        allocation_code: str | None = None,
    ):
        """PATCH .../allocation-sets/<set_code>/allocations/<alloc_code>/override/"""
        serializer = AllocationOverrideSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.override(
            plan_code=code,
            version=version,
            allocation_set_code=allocation_set_code,
            allocation_code=allocation_code,
            override_days=serializer.validated_data["override_days"],
            notes=serializer.validated_data["notes"],
        )
        return self.response(
            data=AllocationSerializer(obj).data,
            message="Allocation override updated successfully.",
        )
