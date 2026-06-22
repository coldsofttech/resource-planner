from rest_framework import serializers

from apps.core.serializers import (
    CodeSerializer,
    ListMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.models import ProjectLink


class ProjectLinkSerializer(ListMixin, CodeSerializer):
    project_code = serializers.CharField(source="project.code", read_only=True)
    title = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectLink
        fields = [
            "code",
            "project_code",
            "title",
            "url",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectLinkCreateSerializer(WriteMixin, serializers.Serializer):
    title = serializers.CharField(max_length=200, required=True)
    url = serializers.URLField(max_length=500, required=True)


class ProjectLinkUpdateSerializer(WriteMixin, serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    url = serializers.URLField(max_length=500, required=False)
