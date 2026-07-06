from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin


class PlaceholderLeaveSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    member_code = serializers.SerializerMethodField()
    member_name = serializers.SerializerMethodField()
    member_avatar_url = serializers.SerializerMethodField()
    sprint_code = serializers.SerializerMethodField()
    sprint_name = serializers.SerializerMethodField()
    days = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_auto = serializers.BooleanField(read_only=True)
    source_display = serializers.SerializerMethodField()
    notes = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_member_code(self, obj) -> str:
        return obj.member.profile.code

    def get_member_name(self, obj) -> str:
        return obj.member.profile.display_name

    def get_member_avatar_url(self, obj) -> str:
        avatars = obj.member.avatars.all()
        if avatars:
            uri = avatars[0].avatar
            if uri.startswith("data:"):
                return uri
        return f"/api/v1/users/{obj.member.profile.code}/avatar/"

    def get_sprint_code(self, obj) -> str:
        return obj.sprint.code

    def get_sprint_name(self, obj) -> str:
        return obj.sprint.name

    def get_source_display(self, obj) -> str:
        return "Auto" if obj.is_auto else "Manual"


class PlaceholderLeaveUpdateSerializer(WriteMixin, serializers.Serializer):
    days = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=True, min_value=0
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )


class PlaceholderLeaveRegenerateSerializer(WriteMixin, serializers.Serializer):
    include_current_sprint = serializers.BooleanField(required=False, default=False)
    remove_overrides = serializers.BooleanField(required=False, default=False)
