from django.contrib.auth import login
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request

from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.viewsets import BaseViewSet
from apps.saml.selectors import get_active_provider_by_code
from apps.saml.serializers import SAMLCreateSerializer, SAMLSerializer
from apps.saml.services import SAMLFlowService, SAMLService


class SAMLViewSet(BaseViewSet):
    service_class = SAMLService

    def get_retrieve_serializer_class(self):
        return SAMLSerializer

    def get_create_serializer_class(self):
        return SAMLCreateSerializer

    def get_create_custom_message(self):
        return "SAML provider created successfully."

    @extend_schema(
        summary="Create SAML provider",
        request=SAMLCreateSerializer,
        responses={
            201: SAMLSerializer,
            400: OpenApiResponse(description="Validation error."),
            409: OpenApiResponse(description="Provider with this name already exists."),
        },
    )
    def create(self, request: Request):
        """POST /auth/saml/"""
        return super().create(request)

    @extend_schema(
        summary="Begin SAML login",
        description=(
            "Builds a SAML AuthnRequest (HTTP-Redirect binding) and returns the "
            "IdP redirect URL. Optional `relay_state` is forwarded through the "
            "SAML flow and echoed back in the ACS response."
        ),
        responses={
            200: OpenApiResponse(description="SAML redirect URL returned."),
            404: OpenApiResponse(description="SAML provider not found or inactive."),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<provider_code>[^/.]+)/authorize",
        url_name="authorize",
    )
    def authorize(self, request: Request, provider_code: str = ""):
        """GET /auth/saml/<provider_code>/authorize/?relay_state=<optional>"""
        relay_state = request.query_params.get("relay_state", "")

        provider = get_active_provider_by_code(provider_code)
        if provider is None:
            raise NotFoundException(
                resource="SAML provider",
                lookup_field="code",
                lookup_value=provider_code,
            )

        svc = SAMLFlowService(user=request.user, request=request)
        redirect_url = svc.build_authorize_url(
            provider=provider, relay_state=relay_state
        )

        return self.response(
            data={"redirect_url": redirect_url},
            message="SAML redirect URL generated.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="SAML Assertion Consumer Service",
        description=(
            "Receives the SAMLResponse form-posted by the IdP (HTTP-POST binding), "
            "validates the XML-DSig signature against the stored IdP certificate, "
            "extracts user attributes, and establishes a local session."
        ),
        responses={
            200: OpenApiResponse(
                description="Login successful. Returns basic user info."
            ),
            400: OpenApiResponse(
                description=(
                    "Validation error — one of: SAMLResponse missing, SAML status not "
                    "success, missing Issuer or NameID, or signature verification "
                    "failed."
                )
            ),
            404: OpenApiResponse(description="SAML provider not found or inactive."),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="acs",
        url_name="acs",
        parser_classes=[FormParser, MultiPartParser],
    )
    def acs(self, request: Request):
        """POST /auth/saml/acs/"""
        saml_response_b64, relay_state = self._extract_acs_params(request)

        svc = SAMLFlowService(user=request.user, request=request)
        user = svc.complete_login(saml_response_b64=saml_response_b64)

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        return self.response(
            data={
                "user": {
                    "id": user.pk,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_superuser": user.is_superuser,
                },
                "relay_state": relay_state,
            },
            message="Login successful.",
            status_code=status.HTTP_200_OK,
        )

    def _extract_acs_params(self, request: Request) -> tuple[str, str]:
        saml_response_b64 = (request.data.get("SAMLResponse") or "").strip()
        relay_state = request.data.get("RelayState", "")
        if not saml_response_b64:
            raise ValidationException("SAMLResponse is required.")
        return saml_response_b64, relay_state
