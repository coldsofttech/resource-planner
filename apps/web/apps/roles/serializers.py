from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.roles.models import Role


class RoleListSerializer(ListMixin, CodeSerializer):
    role = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)
    is_assignable = serializers.BooleanField(read_only=True)
    is_leadership = serializers.BooleanField(read_only=True)
    members_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = Role
        fields = [
            "code",
            "role",
            "is_active",
            "is_default",
            "is_assignable",
            "is_leadership",
            "members_count",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class RoleDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)
    is_assignable = serializers.BooleanField(read_only=True)
    is_leadership = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = Role
        fields = [
            "code",
            "role",
            "is_active",
            "is_default",
            "is_assignable",
            "is_leadership",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class RoleCreateSerializer(WriteMixin, serializers.Serializer):
    role = serializers.CharField(max_length=100, required=True)
    is_active = serializers.BooleanField(default=True, required=False)
    is_default = serializers.BooleanField(default=False, required=False)
    is_assignable = serializers.BooleanField(default=False, required=False)
    is_leadership = serializers.BooleanField(default=False, required=False)


class RoleUpdateSerializer(WriteMixin, serializers.Serializer):
    role = serializers.CharField(max_length=100, required=False)
    is_active = serializers.BooleanField(required=False)
    is_default = serializers.BooleanField(required=False)
    is_assignable = serializers.BooleanField(required=False)
    is_leadership = serializers.BooleanField(required=False)
