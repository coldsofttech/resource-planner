from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin
from apps.tags.serializers import TagCreateSerializer, TagSerializer
from apps.tags.services import TagExportService, TagService


@extend_schema(tags=["Tags"])
class TagViewSet(ExportMixin, BaseViewSet):
    service_class = TagService
    export_service_class = TagExportService

    export_columns = [
        {"key": "name", "label": "Tag", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_permissions(self):
        action_perms = {
            "list": "tags.view_tag",
            "create": "tags.add_tag",
            "export_specs": "tags.export_tag",
            "export": "tags.export_tag",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return TagSerializer

    def list(self, request: Request):
        """GET /api/v1/tags/"""
        return super().list(request)

    def create(self, request: Request):
        """POST /api/v1/tags/"""
        serializer = TagCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(**serializer.validated_data)
        return self.response(
            data=TagSerializer(obj).data,
            message="Tag created successfully.",
            status_code=status.HTTP_201_CREATED,
        )
