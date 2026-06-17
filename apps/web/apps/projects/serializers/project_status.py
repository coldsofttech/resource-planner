from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.models import ProjectStatus, ProjectSubStatus


class ProjectStatusListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectStatus
        fields = [
            "code",
            "name",
            "sort_order",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectStatusDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = ProjectStatus
        fields = [
            "code",
            "name",
            "sort_order",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectSubStatusListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    main_status_code = serializers.CharField(source="main_status.code", read_only=True)
    main_status_name = serializers.CharField(source="main_status.name", read_only=True)
    order = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectSubStatus
        fields = [
            "code",
            "name",
            "main_status_code",
            "main_status_name",
            "order",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectSubStatusDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    main_status_code = serializers.CharField(source="main_status.code", read_only=True)
    main_status_name = serializers.CharField(source="main_status.name", read_only=True)
    order = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = ProjectSubStatus
        fields = [
            "code",
            "name",
            "main_status_code",
            "main_status_name",
            "order",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectSubStatusCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    is_active = serializers.BooleanField(default=True, required=False)


class ProjectSubStatusUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    is_active = serializers.BooleanField(required=False)


class ProjectSubStatusReorderSerializer(WriteMixin, serializers.Serializer):
    codes = serializers.ListField(
        child=serializers.CharField(), required=True, min_length=1
    )
