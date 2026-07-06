from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.resource_plans.serializers import (
    EngineerHirePlaceholderSerializer,
    ManpowerRequestActionSerializer,
    ManpowerRequestHireSerializer,
    ManpowerRequestSerializer,
)
from apps.resource_plans.services import ManpowerRequestService


@extend_schema(tags=["Resource Plans: Manpower Requests"])
class ManpowerRequestViewSet(BaseViewSet):
    service_class = ManpowerRequestService

    def get_permissions(self):
        action_perms = {
            "list": "resource_plans.view_manpowerrequest",
            "retrieve": "resource_plans.view_manpowerrequest",
            "hire": "resource_plans.change_manpowerrequest",
            "rebalance": "resource_plans.change_manpowerrequest",
            "dismiss": "resource_plans.change_manpowerrequest",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List manpower requests for an allocation set",
        responses={200: ManpowerRequestSerializer(many=True)},
    )
    def list(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
    ):
        """GET .../allocation-sets/<allocation_set_code>/manpower-requests/"""
        params = self.get_list_params(request)
        result = self.service.list_for_set(
            plan_code=code,
            version=version,
            allocation_set_code=allocation_set_code,
            params=params,
        )
        return self.paginated_response(
            result=result,
            serializer_class=ManpowerRequestSerializer,
            message="Manpower requests retrieved successfully.",
        )

    @extend_schema(
        summary="Retrieve a manpower request",
        responses={
            200: ManpowerRequestSerializer,
            404: OpenApiResponse(description="Manpower request not found."),
        },
    )
    def retrieve(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
        manpower_request_code: str | None = None,
    ):
        """GET .../manpower-requests/<manpower_request_code>/"""
        obj = self.service.get(
            plan_code=code,
            version=version,
            allocation_set_code=allocation_set_code,
            manpower_request_code=manpower_request_code,
        )
        return self.response(
            data=ManpowerRequestSerializer(obj).data,
            message="Manpower request retrieved successfully.",
        )

    @extend_schema(
        summary="Hire against a manpower request",
        request=ManpowerRequestHireSerializer,
        responses={
            200: EngineerHirePlaceholderSerializer,
            404: OpenApiResponse(description="Manpower request not found."),
        },
    )
    def hire(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
        manpower_request_code: str | None = None,
    ):
        """POST .../manpower-requests/<manpower_request_code>/hire/"""
        serializer = ManpowerRequestHireSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.hire_by_code(
            plan_code=code,
            version=version,
            allocation_set_code=allocation_set_code,
            manpower_request_code=manpower_request_code,
            **serializer.validated_data,
        )
        return self.response(
            data=EngineerHirePlaceholderSerializer(obj).data,
            message="Hire placeholder created successfully.",
        )

    @extend_schema(
        summary="Mark a manpower request as rebalanced",
        request=ManpowerRequestActionSerializer,
        responses={
            200: ManpowerRequestSerializer,
            404: OpenApiResponse(description="Manpower request not found."),
        },
    )
    def rebalance(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
        manpower_request_code: str | None = None,
    ):
        """POST .../manpower-requests/<manpower_request_code>/rebalance/"""
        serializer = ManpowerRequestActionSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.rebalance_by_code(
            plan_code=code,
            version=version,
            allocation_set_code=allocation_set_code,
            manpower_request_code=manpower_request_code,
            **serializer.validated_data,
        )
        return self.response(
            data=ManpowerRequestSerializer(obj).data,
            message="Manpower request rebalanced successfully.",
        )

    @extend_schema(
        summary="Dismiss a manpower request",
        request=ManpowerRequestActionSerializer,
        responses={
            200: ManpowerRequestSerializer,
            404: OpenApiResponse(description="Manpower request not found."),
        },
    )
    def dismiss(
        self,
        request: Request,
        code: str | None = None,
        version: int | None = None,
        allocation_set_code: str | None = None,
        manpower_request_code: str | None = None,
    ):
        """POST .../manpower-requests/<manpower_request_code>/dismiss/"""
        serializer = ManpowerRequestActionSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.dismiss_by_code(
            plan_code=code,
            version=version,
            allocation_set_code=allocation_set_code,
            manpower_request_code=manpower_request_code,
            **serializer.validated_data,
        )
        return self.response(
            data=ManpowerRequestSerializer(obj).data,
            message="Manpower request dismissed successfully.",
        )
