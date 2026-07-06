from __future__ import annotations

from rest_framework import serializers

from apps.core.serializers import (
    CodeSerializer,
    ListMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.resource_plans.models import PlanComment


class ResourcePlanCommentSerializer(ListMixin, CodeSerializer):
    comment = serializers.CharField(source="comment.comment", read_only=True)
    is_edited = serializers.BooleanField(source="comment.is_edited", read_only=True)
    is_pinned = serializers.BooleanField(source="comment.is_pinned", read_only=True)
    mentions = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="comment.created_at", read_only=True)
    created_by = UserMiniSerializer(
        source="comment.created_by", read_only=True, allow_null=True
    )
    updated_at = serializers.DateTimeField(source="comment.updated_at", read_only=True)
    updated_by = UserMiniSerializer(
        source="comment.updated_by", read_only=True, allow_null=True
    )

    class Meta(CodeSerializer.Meta):
        model = PlanComment
        fields = [
            "code",
            "comment",
            "is_edited",
            "is_pinned",
            "mentions",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]

    def get_mentions(self, obj: PlanComment) -> list[dict]:
        return [UserMiniSerializer(m.user).data for m in obj.comment.mentions.all()]


class ResourcePlanCommentCreateSerializer(WriteMixin, serializers.Serializer):
    comment = serializers.CharField()
    mentions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )


class ResourcePlanCommentUpdateSerializer(WriteMixin, serializers.Serializer):
    comment = serializers.CharField(required=False)
    mentions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
