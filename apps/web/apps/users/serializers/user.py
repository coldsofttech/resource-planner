from rest_framework import serializers

from apps.core.serializers import BaseSerializer, UserMiniSerializer, WriteMixin
from apps.users.constants import TIMEZONE_CHOICES, ThemeChoices


class MemberAvatarUrlField(serializers.SerializerMethodField):
    def to_representation(self, value):
        return "/api/v1/users/me/avatar/"


class UpdatePreferencesSerializer(WriteMixin, BaseSerializer):
    theme = serializers.ChoiceField(choices=ThemeChoices.choices)


class UpdateProfileSerializer(WriteMixin, BaseSerializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    display_name = serializers.CharField(
        max_length=150, allow_blank=True, required=False
    )
    timezone = serializers.ChoiceField(choices=TIMEZONE_CHOICES, required=False)
    skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )


class ChangePasswordSerializer(WriteMixin, BaseSerializer):
    current_password = serializers.CharField(min_length=1)
    new_password = serializers.CharField(min_length=12)
    confirm_password = serializers.CharField(min_length=12)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class GroupSummarySerializer(BaseSerializer):
    name = serializers.CharField()
    description = serializers.CharField()


class ResourceRefSerializer(BaseSerializer):
    code = serializers.CharField()
    label = serializers.CharField()


class SkillSummarySerializer(BaseSerializer):
    code = serializers.CharField()
    skill = serializers.CharField()


class UserMeSerializer(BaseSerializer):
    profile_code = serializers.CharField(allow_null=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    display_name = serializers.CharField()
    theme = serializers.CharField()
    timezone = serializers.CharField()
    avatar_url = serializers.CharField(allow_null=True)
    is_sso = serializers.BooleanField()
    sso_provider_name = serializers.CharField(allow_null=True)
    is_classic = serializers.BooleanField()
    last_login = serializers.DateTimeField(allow_null=True)
    password_last_changed = serializers.DateTimeField(allow_null=True)
    groups = GroupSummarySerializer(many=True)
    location = ResourceRefSerializer(allow_null=True)
    employment_type = ResourceRefSerializer(allow_null=True)
    role = ResourceRefSerializer(allow_null=True)
    skills = SkillSummarySerializer(many=True)


class UserAdminListSerializer(BaseSerializer):
    """Serializes a UserProfile instance for the admin users list."""

    code = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    is_superuser = serializers.BooleanField(source="user.is_superuser", read_only=True)
    must_change_password = serializers.BooleanField(read_only=True)
    auth_type = serializers.SerializerMethodField()
    hide_reset_password = serializers.SerializerMethodField()
    last_login = serializers.DateTimeField(
        source="user.last_login", read_only=True, allow_null=True
    )
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

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

    def get_hide_reset_password(self, obj) -> bool:
        if obj.user.is_superuser:
            return True
        return obj.sso_provider_content_type is not None


class UserAdminCreateSerializer(WriteMixin, BaseSerializer):
    first_name = serializers.CharField(min_length=1, max_length=150)
    last_name = serializers.CharField(min_length=1, max_length=150)
    email = serializers.EmailField()


class UserAdminDetailSerializer(UserAdminListSerializer):
    """Extended user serializer for the detail endpoint — adds profile fields."""

    groups = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    employment_type = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    def get_groups(self, obj) -> list:
        result = []
        for g in obj.user.groups.all():
            profile = getattr(g, "profile", None)
            result.append({"name": g.name, "code": profile.code if profile else ""})
        return result

    def get_location(self, obj) -> dict | None:
        if obj.location:
            return {
                "code": obj.location.code,
                "label": f"{obj.location.city}, {obj.location.country}",
            }
        return None

    def get_employment_type(self, obj) -> dict | None:
        if obj.employment_type:
            return {"code": obj.employment_type.code, "label": obj.employment_type.name}
        return None

    def get_role(self, obj) -> dict | None:
        if obj.role:
            return {"code": obj.role.code, "label": obj.role.role}
        return None

    def get_avatar_url(self, obj) -> str:
        return f"/api/v1/users/{obj.code}/avatar/"
