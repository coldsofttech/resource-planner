from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny

from apps.core.viewsets import BaseViewSet
from apps.meta.serializers import MetaSerializer
from apps.meta.services import MetaService


class MetaViewSet(BaseViewSet):
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]

    @extend_schema(
        summary="Retrieve application metadata",
        description=(
            "Returns public application metadata (app name, auth mode, "
            "registration policy). When the request carries a valid session "
            "cookie the response also includes the authenticated user's profile."
        ),
        responses={
            200: OpenApiResponse(
                response=MetaSerializer,
                description="Metadata retrieved successfully.",
            ),
        },
    )
    def list(self, request):
        data = MetaService.get_meta(request.user)
        return self.response(data=data, message="Meta fetched.")
