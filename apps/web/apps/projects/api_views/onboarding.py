from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from apps.core.viewsets import BaseViewSet
from apps.projects.serializers.onboarding import (
    OnboardingDetailSerializer,
    OnboardingSubmitSerializer,
)
from apps.projects.services import OnboardingService


@extend_schema(tags=["Onboarding"])
class OnboardingViewSet(BaseViewSet):
    """Public-only viewset for the demand request portal.

    No authentication is required for any action here.
    Authenticated/review actions live in DemandsViewSet.
    """

    def get_authenticators(self):
        return []

    def get_permissions(self):
        return [AllowAny()]

    @extend_schema(
        summary="Submit a demand request (public)",
        request=OnboardingSubmitSerializer,
        responses={
            201: OnboardingDetailSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def submit(self, request: Request):
        """POST /onboarding/submit/"""
        serializer = OnboardingSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        svc = OnboardingService()
        obj = svc.submit(
            project_name=data["project_name"],
            requester_email=data["requester_email"],
            requirements=data.get("requirements", ""),
            risk=data.get("risk", ""),
            project_code=data.get("project_code", ""),
            tentative_start_date=data.get("tentative_start_date"),
            tentative_end_date=data.get("tentative_end_date"),
            product_codes=data.get("product_codes") or [],
            business_unit_codes=data.get("business_unit_codes") or [],
            accountable_executive_email=data.get("accountable_executive_email") or "",
            contact_emails=data.get("contact_emails") or [],
            links=data.get("links") or [],
        )
        return self.response(
            data=OnboardingDetailSerializer(obj).data,
            message="Demand request submitted successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Onboarding options (public)",
        description=(
            "Returns active business units and products for the public "
            "onboarding portal."
        ),
        responses={
            200: OpenApiResponse(description="Business units and products options.")
        },
    )
    def options(self, request: Request):
        """GET /onboarding/options/"""
        from apps.business_units.models import BusinessUnit
        from apps.products.models import Product

        business_units = list(
            BusinessUnit.objects.filter(is_active=True)
            .order_by("name")
            .values("code", "name")
        )
        products = list(
            Product.objects.filter(is_active=True)
            .order_by("name")
            .values("code", "name")
        )
        return self.response(
            data={"business_units": business_units, "products": products},
            message="Onboarding options retrieved successfully.",
        )

    @extend_schema(
        summary="Onboarding stats (public)",
        responses={200: OpenApiResponse(description="Stats response.")},
    )
    def stats(self, request: Request):
        """GET /onboarding/stats/"""
        svc = OnboardingService()
        data = svc.stats()
        return self.response(data=data, message="Stats retrieved successfully.")
