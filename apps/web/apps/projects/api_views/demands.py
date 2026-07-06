from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.auth.authentication import BearerTokenAuthentication
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers.onboarding import (
    OnboardingDetailSerializer,
    OnboardingListSerializer,
)
from apps.projects.services import OnboardingReviewService, OnboardingService


@extend_schema(tags=["Demands"])
class DemandsViewSet(BaseViewSet):
    """Private viewset for reviewing and managing demand requests.

    Requires authentication (Bearer token or session).
    Public submission actions live in OnboardingViewSet.
    """

    def get_authenticators(self):
        return [BearerTokenAuthentication(), SessionAuthentication()]

    def get_permissions(self):
        return [IsAuthenticated()]

    @extend_schema(
        summary="List demand requests",
        responses={200: OnboardingListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /demands/"""
        params = self.get_list_params(request)
        svc = OnboardingService()
        result = svc.list(params=params)
        return self.paginated_response(
            result=result,
            serializer_class=OnboardingListSerializer,
            message="Demand requests retrieved successfully.",
        )

    @extend_schema(
        summary="Retrieve a demand request",
        responses={
            200: OnboardingDetailSerializer,
            404: OpenApiResponse(description="Not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /demands/<code>/"""
        svc = OnboardingService()
        obj = svc.get(code=code)
        return self.response(data=OnboardingDetailSerializer(obj).data)

    @extend_schema(
        summary="Accept a demand request",
        responses={
            200: OnboardingDetailSerializer,
            404: OpenApiResponse(description="Not found."),
            400: OpenApiResponse(description="Cannot accept."),
        },
    )
    def accept(self, request: Request, code=None):
        """POST /demands/<code>/accept/"""
        review_svc = OnboardingReviewService(user=request.user)
        obj = review_svc.accept(code=code)
        return self.response(
            data=OnboardingDetailSerializer(obj).data,
            message="Demand request accepted and project created.",
        )

    @extend_schema(
        summary="Reject a demand request",
        responses={
            200: OnboardingDetailSerializer,
            404: OpenApiResponse(description="Not found."),
            400: OpenApiResponse(description="Cannot reject."),
        },
    )
    def reject(self, request: Request, code=None):
        """POST /demands/<code>/reject/"""
        review_svc = OnboardingReviewService(user=request.user)
        obj = review_svc.reject(code=code)
        return self.response(
            data=OnboardingDetailSerializer(obj).data,
            message="Demand request rejected.",
        )
