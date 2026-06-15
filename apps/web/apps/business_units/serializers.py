from rest_framework import serializers

from apps.business_units.models import BusinessUnit
from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)


class BusinessUnitListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    short_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = BusinessUnit
        fields = [
            "code",
            "name",
            "short_name",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class BusinessUnitDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    short_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = BusinessUnit
        fields = [
            "code",
            "name",
            "short_name",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class BusinessUnitCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    short_name = serializers.CharField(max_length=10, required=True)
    is_active = serializers.BooleanField(default=True, required=False)


class BusinessUnitUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    short_name = serializers.CharField(max_length=10, required=False)
    is_active = serializers.BooleanField(required=False)
