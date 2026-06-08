from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.employment_types.models import EmploymentType


class EmploymentTypeListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = EmploymentType
        fields = [
            "code",
            "name",
            "is_active",
            "is_default",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class EmploymentTypeDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = EmploymentType
        fields = [
            "code",
            "name",
            "is_active",
            "is_default",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class EmploymentTypeCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    is_active = serializers.BooleanField(default=True, required=False)
    is_default = serializers.BooleanField(default=False, required=False)


class EmploymentTypeUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    is_active = serializers.BooleanField(required=False)
    is_default = serializers.BooleanField(required=False)
