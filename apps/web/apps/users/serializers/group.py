from rest_framework import serializers

from apps.core.serializers import BaseSerializer, UserMiniSerializer, WriteMixin


class GroupAdminListSerializer(BaseSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(source="group.name", read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_admin_group = serializers.BooleanField(read_only=True)
    is_system = serializers.BooleanField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)


class GroupMemberSerializer(BaseSerializer):
    code = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    avatar_url = serializers.SerializerMethodField()
    auth_type = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        avatars = obj.user.avatars.all()
        if avatars:
            uri = avatars[0].avatar
            if uri.startswith("data:"):
                return uri
        return f"/api/v1/users/{obj.code}/avatar/"

    def get_auth_type(self, obj) -> str:
        ct = obj.sso_provider_content_type
        if ct is None:
            return "classic"
        app_label = ct.app_label
        if app_label == "oauth":
            return "oauth"
        if app_label == "saml":
            return "saml"
        return app_label


class GroupCreateSerializer(WriteMixin, BaseSerializer):
    name = serializers.CharField(min_length=1, max_length=150)
    description = serializers.CharField(required=False, allow_blank=True, default="")


class GroupUpdateSerializer(WriteMixin, BaseSerializer):
    name = serializers.CharField(min_length=1, max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class GroupAssignMemberSerializer(WriteMixin, BaseSerializer):
    member_code = serializers.CharField()
