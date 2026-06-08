from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.locations.models import Location


class LocationListSerializer(ListMixin, CodeSerializer):
    city = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = Location
        fields = [
            "code",
            "city",
            "country",
            "is_active",
            "is_default",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class LocationDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = Location
        fields = [
            "code",
            "city",
            "country",
            "is_active",
            "is_default",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class LocationCreateSerializer(WriteMixin, serializers.Serializer):
    city = serializers.CharField(max_length=100, required=True)
    country = serializers.CharField(max_length=100, required=True)
    is_active = serializers.BooleanField(default=True, required=False)
    is_default = serializers.BooleanField(default=False, required=False)


class LocationUpdateSerializer(WriteMixin, serializers.Serializer):
    city = serializers.CharField(max_length=100, required=False)
    country = serializers.CharField(max_length=100, required=False)
    is_active = serializers.BooleanField(required=False)
    is_default = serializers.BooleanField(required=False)
