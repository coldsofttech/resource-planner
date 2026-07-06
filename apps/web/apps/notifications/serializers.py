from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    WriteMixin,
)
from apps.notifications.constants import (
    NON_SUPPRESSIBLE_CATEGORIES,
    NotificationCategory,
    NotificationType,
)
from apps.notifications.models import Notification, NotificationPreference


class NotificationListSerializer(ListMixin, CodeSerializer):
    title = serializers.CharField(read_only=True)
    body = serializers.CharField(read_only=True)
    link = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    notification_type = serializers.CharField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)
    is_dismissed = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta(CodeSerializer.Meta):
        model = Notification
        fields = [
            "code",
            "title",
            "body",
            "link",
            "category",
            "notification_type",
            "is_read",
            "is_dismissed",
            "created_at",
        ]


class NotificationDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    body = serializers.CharField(read_only=True)
    link = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    notification_type = serializers.CharField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)
    is_dismissed = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = Notification
        fields = [
            "code",
            "title",
            "body",
            "link",
            "category",
            "notification_type",
            "is_read",
            "is_dismissed",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class NotificationCreateSerializer(WriteMixin, serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    body = serializers.CharField(required=True)
    link = serializers.CharField(
        max_length=200, required=False, default="", allow_blank=True
    )
    category = serializers.ChoiceField(
        choices=NotificationCategory.choices,
        required=False,
        default=NotificationCategory.GENERAL,
    )
    notification_type = serializers.ChoiceField(
        choices=NotificationType.choices,
        required=False,
        default=NotificationType.INFO,
    )


class NotificationPreferenceSerializer(ListMixin, CodeSerializer):
    category = serializers.CharField(read_only=True)
    category_label = serializers.SerializerMethodField()
    is_enabled = serializers.BooleanField(read_only=True)
    is_suppressible = serializers.SerializerMethodField()

    def get_category_label(self, obj: NotificationPreference) -> str:
        return NotificationCategory(obj.category).label

    def get_is_suppressible(self, obj: NotificationPreference) -> bool:
        return obj.category not in NON_SUPPRESSIBLE_CATEGORIES

    class Meta(CodeSerializer.Meta):
        model = NotificationPreference
        fields = ["code", "category", "category_label", "is_enabled", "is_suppressible"]


class NotificationPreferenceUpdateSerializer(WriteMixin, serializers.Serializer):
    is_enabled = serializers.BooleanField(required=True)
