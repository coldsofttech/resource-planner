from rest_framework import serializers

from apps.core.serializers import CodeSerializer, ListMixin, UserMiniSerializer
from apps.tags.models import Tag


class TagCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)


class TagSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = Tag
        fields = [
            "code",
            "name",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
