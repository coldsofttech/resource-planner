from rest_framework import serializers

from apps.core.serializers import (
    CodeSerializer,
    ListMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.models import ProjectFollower


class ProjectFollowerListSerializer(ListMixin, CodeSerializer):
    user_code = serializers.CharField(source="user.profile.code", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_user_name(self, obj) -> str:
        parts = [obj.user.first_name, obj.user.last_name]
        return " ".join(p for p in parts if p) or obj.user.email

    class Meta(CodeSerializer.Meta):
        model = ProjectFollower
        fields = [
            "code",
            "user_code",
            "user_email",
            "user_name",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectFollowerCreateSerializer(WriteMixin, serializers.Serializer):
    user_code = serializers.CharField(required=True)


class ProjectFollowerUpdateSerializer(WriteMixin, serializers.Serializer):
    user_code = serializers.CharField(required=False)
