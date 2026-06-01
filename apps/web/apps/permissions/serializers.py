from rest_framework import serializers

from apps.core.serializers import (
    BaseSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    WriteMixin,
)
from apps.permissions.constants import PermissionScope
from apps.permissions.models import (
    GroupPermissionCategory,
    PermissionCategory,
    UserPermissionCategory,
)


class PermissionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    codename = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class PermissionCategoryListSerializer(ListMixin, CodeSerializer):
    module = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    codename = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    order = serializers.IntegerField(read_only=True)

    class Meta(CodeSerializer.Meta):
        model = PermissionCategory
        fields = ["code", "module", "name", "codename", "label", "order"]


class PermissionCategoryMiniSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    module = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)


class PermissionCategoryDetailSerializer(ReadMixin, CodeSerializer):
    module = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    codename = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    order = serializers.IntegerField(read_only=True)
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta(CodeSerializer.Meta):
        model = PermissionCategory
        fields = ["code", "module", "name", "codename", "label", "order", "permissions"]


class GroupPermissionCategorySerializer(ListMixin, CodeSerializer):
    category = PermissionCategoryMiniSerializer(read_only=True)
    scope = serializers.IntegerField(read_only=True)
    scope_display = serializers.CharField(source="get_scope_display", read_only=True)
    granted_at = serializers.DateTimeField(read_only=True)

    class Meta(CodeSerializer.Meta):
        model = GroupPermissionCategory
        fields = ["code", "category", "scope", "scope_display", "granted_at"]


class GroupPermissionCategoryAssignSerializer(WriteMixin, BaseSerializer):
    category_code = serializers.CharField(required=True)
    scope = serializers.ChoiceField(choices=PermissionScope.choices, required=True)


class GroupPermissionCategoryUpdateSerializer(WriteMixin, BaseSerializer):
    scope = serializers.ChoiceField(choices=PermissionScope.choices, required=True)


class UserPermissionCategorySerializer(ListMixin, CodeSerializer):
    category = PermissionCategoryMiniSerializer(read_only=True)
    scope = serializers.IntegerField(read_only=True)
    scope_display = serializers.CharField(source="get_scope_display", read_only=True)
    granted_at = serializers.DateTimeField(read_only=True)

    class Meta(CodeSerializer.Meta):
        model = UserPermissionCategory
        fields = ["code", "category", "scope", "scope_display", "granted_at"]


class UserPermissionCategoryAssignSerializer(WriteMixin, BaseSerializer):
    category_code = serializers.CharField(required=True)
    scope = serializers.ChoiceField(choices=PermissionScope.choices, required=True)


class UserPermissionCategoryUpdateSerializer(WriteMixin, BaseSerializer):
    scope = serializers.ChoiceField(choices=PermissionScope.choices, required=True)


class UserEffectivePermissionSerializer(serializers.Serializer):
    category = PermissionCategoryMiniSerializer(read_only=True)
    scope = serializers.IntegerField(read_only=True)
    scope_display = serializers.SerializerMethodField()
    via = serializers.CharField(read_only=True)

    def get_scope_display(self, obj) -> str:
        return PermissionScope(obj["scope"]).label
