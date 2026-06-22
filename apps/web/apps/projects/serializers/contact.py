from rest_framework import serializers

from apps.core.serializers import (
    CodeSerializer,
    ListMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.constants import ContactRole
from apps.projects.models import ProjectContact


class ProjectContactSerializer(ListMixin, CodeSerializer):
    contact_code = serializers.CharField(source="contact.code", read_only=True)
    contact_name = serializers.CharField(source="contact.name", read_only=True)
    contact_email = serializers.EmailField(source="contact.email", read_only=True)
    role = serializers.CharField(read_only=True)
    role_display = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectContact
        fields = [
            "code",
            "contact_code",
            "contact_name",
            "contact_email",
            "role",
            "role_display",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]

    def get_role_display(self, obj: ProjectContact) -> str:
        return ContactRole(obj.role).label if obj.role else ""


class ProjectContactCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(allow_blank=True, default="")
    role = serializers.ChoiceField(choices=ContactRole.choices)
