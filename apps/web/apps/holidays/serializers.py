from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.holidays.models import Holiday


class LocationBriefSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True)


class HolidayListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    date = serializers.DateField(read_only=True)
    location = LocationBriefSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = Holiday
        fields = [
            "code",
            "name",
            "date",
            "location",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class HolidayDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    date = serializers.DateField(read_only=True)
    location = LocationBriefSerializer(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = Holiday
        fields = [
            "code",
            "name",
            "date",
            "location",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class HolidayCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=120, required=True)
    date = serializers.DateField(required=True)
    location_code = serializers.CharField(max_length=50, required=True)


class HolidayUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False)
    date = serializers.DateField(required=False)
    location_code = serializers.CharField(max_length=50, required=False)
