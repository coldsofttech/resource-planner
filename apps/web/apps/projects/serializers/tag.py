from rest_framework import serializers

from apps.core.serializers import (
    CodeSerializer,
    ListMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.models import ProjectTag


class ProjectTagSerializer(ListMixin, CodeSerializer):
    tag_code = serializers.CharField(source="tag.code", read_only=True)
    tag_name = serializers.CharField(source="tag.name", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectTag
        fields = [
            "code",
            "tag_code",
            "tag_name",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectTagCreateSerializer(WriteMixin, serializers.Serializer):
    tag_code = serializers.CharField(required=False, allow_blank=False)
    tag_name = serializers.CharField(required=False, allow_blank=False)

    def validate(self, data: dict) -> dict:
        if not data.get("tag_code") and not data.get("tag_name"):
            raise serializers.ValidationError(
                {"tag_name": "Either tag_code or tag_name is required."}
            )
        return data


class ProjectTagUpdateSerializer(WriteMixin, serializers.Serializer):
    tag_code = serializers.CharField(required=False)
