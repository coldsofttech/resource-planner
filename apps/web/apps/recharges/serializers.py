from __future__ import annotations

import re

from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.recharges.models import ProjectTypeMapping, RechargeType

_UPPER_SNAKE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class RechargeTypeListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = RechargeType
        fields = [
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class RechargeTypeDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = RechargeType
        fields = [
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class RechargeTypeCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=50, required=True)
    description = serializers.CharField(default="", required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True, required=False)

    def validate_name(self, value: str) -> str:
        if not _UPPER_SNAKE_RE.match(value):
            raise serializers.ValidationError(
                "Name must be UPPER_SNAKE_CASE (e.g. PROJECT, BAU, HOLIDAY)."
            )
        return value


class RechargeTypeUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=50, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

    def validate_name(self, value: str) -> str:
        if not _UPPER_SNAKE_RE.match(value):
            raise serializers.ValidationError(
                "Name must be UPPER_SNAKE_CASE (e.g. PROJECT, BAU, HOLIDAY)."
            )
        return value


class _ProjectTypeNestedSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class ProjectTypeMappingListSerializer(ListMixin, serializers.ModelSerializer):
    project_type = _ProjectTypeNestedSerializer(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta:
        model = ProjectTypeMapping
        fields = [
            "id",
            "project_type",
            "created_at",
            "created_by",
        ]


class ProjectTypeMappingDetailSerializer(ReadMixin, serializers.ModelSerializer):
    project_type = _ProjectTypeNestedSerializer(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta:
        model = ProjectTypeMapping
        fields = [
            "id",
            "project_type",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectTypeMappingCreateSerializer(WriteMixin, serializers.Serializer):
    project_type_code = serializers.CharField(required=True, max_length=50)


class ProjectTypeMappingUpdateSerializer(WriteMixin, serializers.Serializer):
    project_type_code = serializers.CharField(required=True, max_length=50)
