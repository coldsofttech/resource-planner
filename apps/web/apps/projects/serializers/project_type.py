from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.models import ProjectType


class ProjectTypeListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_protected = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectType
        fields = [
            "code",
            "name",
            "description",
            "is_active",
            "is_protected",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectTypeDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_protected = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = ProjectType
        fields = [
            "code",
            "name",
            "description",
            "is_active",
            "is_protected",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectTypeCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=60, required=True)
    description = serializers.CharField(default="", required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True, required=False)


class ProjectTypeUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=60, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
