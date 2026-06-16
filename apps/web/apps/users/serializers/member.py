from rest_framework import serializers

from apps.core.serializers import BaseSerializer, UserMiniSerializer, WriteMixin


class MemberMiniListSerializer(BaseSerializer):
    """
    Compact member representation for resource-scoped
    member lists (teams, skills, roles, etc.).
    """

    code = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    avatar_url = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    employment_type = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    teams = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        avatars = obj.user.avatars.all()
        if avatars:
            uri = avatars[0].avatar
            if uri.startswith("data:"):
                return uri
        return f"/api/v1/users/{obj.code}/avatar/"

    def get_location(self, obj):
        if obj.location:
            return {
                "code": obj.location.code,
                "label": f"{obj.location.city}, {obj.location.country}",
            }
        return None

    def get_employment_type(self, obj):
        if obj.employment_type:
            return {"code": obj.employment_type.code, "label": obj.employment_type.name}
        return None

    def get_role(self, obj):
        if obj.role:
            return {
                "code": obj.role.code,
                "label": obj.role.role,
                "is_leadership": obj.role.is_leadership,
            }
        return None

    def get_teams(self, obj):
        return [
            {"code": a.team.code, "name": a.team.name}
            for a in obj.user.team_assignments.all()
        ]


class MemberListSerializer(BaseSerializer):
    """Serializes a UserProfile instance for the members list."""

    code = serializers.CharField(read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    display_name = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    location = serializers.SerializerMethodField()
    employment_type = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    teams = serializers.SerializerMethodField()
    joined_date = serializers.DateField(read_only=True, allow_null=True)
    leaving_date = serializers.DateField(read_only=True, allow_null=True)
    default_holidays = serializers.IntegerField(read_only=True, allow_null=True)
    skills = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_avatar_url(self, obj):
        avatars = obj.user.avatars.all()
        if avatars:
            uri = avatars[0].avatar
            if uri.startswith("data:"):
                return uri
        return f"/api/v1/users/{obj.code}/avatar/"

    def get_location(self, obj):
        if obj.location:
            return {
                "code": obj.location.code,
                "label": f"{obj.location.city}, {obj.location.country}",
            }
        return None

    def get_employment_type(self, obj):
        if obj.employment_type:
            return {"code": obj.employment_type.code, "label": obj.employment_type.name}
        return None

    def get_role(self, obj):
        if obj.role:
            return {
                "code": obj.role.code,
                "label": obj.role.role,
                "is_leadership": obj.role.is_leadership,
            }
        return None

    def get_teams(self, obj):
        return [
            {"code": a.team.code, "name": a.team.name}
            for a in obj.user.team_assignments.all()
        ]

    def get_skills(self, obj):
        return [{"code": s.code, "skill": s.skill} for s in obj.skills.all()]


class AssignMemberSerializer(WriteMixin, BaseSerializer):
    teams = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list,
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")


class MemberUpdateSerializer(WriteMixin, BaseSerializer):
    location = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    employment_type = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    role = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    joined_date = serializers.DateField(required=False, allow_null=True)
    leaving_date = serializers.DateField(required=False, allow_null=True)
    default_holidays = serializers.IntegerField(
        required=False, allow_null=True, min_value=0
    )
