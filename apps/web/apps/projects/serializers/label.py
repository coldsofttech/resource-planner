from rest_framework import serializers

from apps.core.serializers import (
    CodeSerializer,
    ListMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.models import ProjectLabel

_LABEL_REGEX = r"^[A-Z0-9_]+$"
_LABEL_FORMAT_MSG = (
    "Label must contain only uppercase letters (A-Z), digits (0-9), "
    "and underscores (_)."
)


class ProjectLabelSerializer(ListMixin, CodeSerializer):
    label = serializers.CharField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectLabel
        fields = [
            "code",
            "label",
            "is_default",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectLabelCreateSerializer(WriteMixin, serializers.Serializer):
    label = serializers.RegexField(
        regex=_LABEL_REGEX,
        max_length=50,
        required=True,
        error_messages={"invalid": _LABEL_FORMAT_MSG},
    )
    is_default = serializers.BooleanField(default=False, required=False)


class ProjectLabelUpdateSerializer(WriteMixin, serializers.Serializer):
    label = serializers.RegexField(
        regex=_LABEL_REGEX,
        max_length=50,
        required=False,
        error_messages={"invalid": _LABEL_FORMAT_MSG},
    )
    is_default = serializers.BooleanField(required=False)
