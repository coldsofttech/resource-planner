from drf_spectacular.utils import extend_schema

from apps.core.viewsets import BaseViewSet
from apps.saml.serializers import SAMLCreateSerializer, SAMLSerializer
from apps.saml.services import SAMLService


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
        responses=SAMLSerializer,
    )
    def create(self, request):
        """POST /auth/saml/"""
        return super().create(request)
