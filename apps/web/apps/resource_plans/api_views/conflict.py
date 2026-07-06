from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    ConflictResolveSerializer,
    ConflictSerializer,
)
from apps.resource_plans.services import ConflictService


@extend_schema(tags=["Resource Plans: Conflicts"])
class ConflictViewSet(BaseViewSet):
    service_class = ConflictService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_conflict",
            "retrieve": "resource_plans.view_conflict",
            "resolve": "resource_plans.change_conflict",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List conflicts for an allocation set",
        responses={200: ConflictSerializer(many=True)},
    )
    def list(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
    ):
        """GET .../allocation-sets/<allocation_set_code>/conflicts/"""
        params = self.get_list_params(request)
        result = self.service.list_for_set(
            plan_code=code,
            version=version,
            allocation_set_code=allocation_set_code,
            params=params,
        )
        return self.paginated_response(
            result=result,
            serializer_class=ConflictSerializer,
            message="Conflicts retrieved successfully.",
        )

    @extend_schema(
        summary="Retrieve a conflict",
        responses={
            200: ConflictSerializer,
            404: OpenApiResponse(description="Conflict not found."),
        },
    )
    def retrieve(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
        conflict_code: str | None = None,
    ):
        """GET .../conflicts/<conflict_code>/"""
        obj = self.service.get(
            plan_code=code,
            version=version,
            allocation_set_code=allocation_set_code,
            conflict_code=conflict_code,
        )
        return self.response(
            data=ConflictSerializer(obj).data,
            message="Conflict retrieved successfully.",
        )

    @extend_schema(
        summary="Resolve a conflict",
        request=ConflictResolveSerializer,
        responses={
            200: ConflictSerializer,
            404: OpenApiResponse(description="Conflict not found."),
            422: OpenApiResponse(
                description="Invalid resolution for this conflict type."
            ),
        },
    )
    def resolve(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
        conflict_code: str | None = None,
    ):
        """POST .../conflicts/<conflict_code>/resolve/"""
        serializer = ConflictResolveSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.resolve(
            plan_code=code,
            version=version,
            allocation_set_code=allocation_set_code,
            conflict_code=conflict_code,
            **serializer.validated_data,
        )
        return self.response(
            data=ConflictSerializer(obj).data,
            message="Conflict resolved successfully.",
        )
