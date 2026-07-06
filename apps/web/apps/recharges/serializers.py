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
from apps.recharges.models import ProjectTypeMapping, RechargeProjectGroup, RechargeType

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


class _ProjectNestedSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)


class RechargeProjectGroupListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    projects = _ProjectNestedSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = RechargeProjectGroup
        fields = [
            "code",
            "name",
            "projects",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class RechargeProjectGroupDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    projects = _ProjectNestedSerializer(many=True, read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = RechargeProjectGroup
        fields = [
            "code",
            "name",
            "projects",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class RechargeProjectGroupCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    project_codes = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        allow_empty=True,
    )


class RechargeProjectGroupUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    project_codes = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
    )


class RechargeEmailGroupSerializer(ReadMixin, serializers.Serializer):
    email_code = serializers.CharField(allow_null=True)
    group_code = serializers.CharField()
    group_name = serializers.CharField()
    total_days = serializers.CharField()
    total_cost = serializers.CharField()
    project_count = serializers.IntegerField()
    status = serializers.CharField()
    sent_at = serializers.CharField(allow_null=True)
    to = serializers.ListField(child=serializers.DictField())
    cc = serializers.ListField(child=serializers.DictField())
    subject = serializers.CharField()
    body = serializers.CharField()


class RechargeEmailTriggerSerializer(WriteMixin, serializers.Serializer):
    sprint = serializers.CharField(max_length=50, required=True)
    type = serializers.ChoiceField(choices=["forecast", "actual"], required=True)
