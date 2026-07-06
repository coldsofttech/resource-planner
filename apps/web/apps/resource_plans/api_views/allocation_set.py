from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import AllocationSetSerializer
from apps.resource_plans.services import AllocationSetService


@extend_schema(tags=["Resource Plans: Allocation Sets"])
class AllocationSetViewSet(BaseViewSet):
    service_class = AllocationSetService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_allocationset",
            "retrieve": "resource_plans.view_allocationset",
            "activate": "resource_plans.change_allocationset",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List allocation sets for a resource plan version",
        responses={200: AllocationSetSerializer(many=True)},
    )
    def list(
        self, request: Request, code: str | None = None, version: int | None = None
    ):
        """GET .../versions/<version>/allocation-sets/"""
        objs = self.service.list_for_version(plan_code=code, version=version)
        return self.response(
            data=AllocationSetSerializer(objs, many=True).data,
            message="Allocation sets retrieved successfully.",
        )

    @extend_schema(
        summary="Retrieve an allocation set",
        responses={
            200: AllocationSetSerializer,
            404: OpenApiResponse(description="Allocation set not found."),
        },
    )
    def retrieve(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
    ):
        """GET .../versions/<version>/allocation-sets/<allocation_set_code>/"""
        obj = self.service.get(
            plan_code=code, version=version, allocation_set_code=allocation_set_code
        )
        return self.response(
            data=AllocationSetSerializer(obj).data,
            message="Allocation set retrieved successfully.",
        )

    @extend_schema(
        summary="Activate a draft allocation set",
        responses={
            200: AllocationSetSerializer,
            404: OpenApiResponse(description="Allocation set not found."),
            422: OpenApiResponse(
                description="Only a draft allocation set can be activated."
            ),
        },
    )
    def activate(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
    ):
        """POST .../versions/<version>/allocation-sets/<set_code>/activate/"""
        obj = self.service.activate(
            plan_code=code, version=version, allocation_set_code=allocation_set_code
        )
        return self.response(
            data=AllocationSetSerializer(obj).data,
            message="Allocation set activated successfully.",
        )
