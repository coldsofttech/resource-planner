from drf_spectacular.utils import extend_schema

from apps.core.viewsets import BaseViewSet
from apps.oauth.serializers import OAuthCreateSerializer, OAuthSerializer
from apps.oauth.services import OAuthService


class OAuthViewSet(BaseViewSet):
    service_class = OAuthService

    def get_retrieve_serializer_class(self):
        return OAuthSerializer

    def get_create_serializer_class(self):
        return OAuthCreateSerializer

    def get_create_custom_message(self):
        return "OAuth provider created successfully."

    @extend_schema(
        summary="Create OAuth provider",
        request=OAuthCreateSerializer,
        responses=OAuthSerializer,
    )
    def create(self, request):
        """POST /auth/oauth/"""
        return super().create(request)
