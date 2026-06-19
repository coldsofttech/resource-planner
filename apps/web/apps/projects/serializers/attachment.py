from rest_framework import serializers

from apps.core.serializers import CodeSerializer, ListMixin, UserMiniSerializer
from apps.projects.models import ProjectAttachment


class ProjectAttachmentSerializer(ListMixin, CodeSerializer):
    project_code = serializers.CharField(source="project.code", read_only=True)
    file_name = serializers.CharField(read_only=True)
    content_type = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectAttachment
        fields = [
            "code",
            "project_code",
            "file_name",
            "content_type",
            "file_size",
            "created_at",
            "created_by",
        ]
