from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.to_do.constants import TodoPriority, TodoRecurrenceRule, TodoReminderCategory
from apps.to_do.models import Todo, TodoPreference


class TodoListSerializer(ListMixin, CodeSerializer):
    title = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority = serializers.CharField(read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    group = serializers.CharField(read_only=True)
    due_date = serializers.DateField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    assigned_to = UserMiniSerializer(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta(CodeSerializer.Meta):
        model = Todo
        fields = [
            "code",
            "title",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "group",
            "due_date",
            "is_overdue",
            "assigned_to",
            "created_at",
        ]


class TodoDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority = serializers.CharField(read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    group = serializers.CharField(read_only=True)
    due_date = serializers.DateField(read_only=True)
    reminder_at = serializers.DateTimeField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    assigned_to = UserMiniSerializer(read_only=True, allow_null=True)
    is_recurring = serializers.BooleanField(read_only=True)
    recurrence_rule = serializers.CharField(read_only=True)
    recurrence_interval = serializers.IntegerField(read_only=True)
    recurrence_end_date = serializers.DateField(read_only=True)
    source = serializers.CharField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = Todo
        fields = [
            "code",
            "title",
            "description",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "group",
            "due_date",
            "reminder_at",
            "is_overdue",
            "assigned_to",
            "is_recurring",
            "recurrence_rule",
            "recurrence_interval",
            "recurrence_end_date",
            "source",
            "completed_at",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class TodoCreateSerializer(WriteMixin, serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    priority = serializers.ChoiceField(
        choices=TodoPriority.choices, required=False, default=TodoPriority.MEDIUM
    )
    group = serializers.CharField(
        max_length=100, required=False, default="", allow_blank=True
    )
    due_date = serializers.DateField(required=False, allow_null=True, default=None)
    reminder_at = serializers.DateTimeField(
        required=False, allow_null=True, default=None
    )
    is_recurring = serializers.BooleanField(required=False, default=False)
    recurrence_rule = serializers.ChoiceField(
        choices=TodoRecurrenceRule.choices,
        required=False,
        default="",
        allow_blank=True,
    )
    recurrence_interval = serializers.IntegerField(
        required=False, default=1, min_value=1
    )
    recurrence_end_date = serializers.DateField(
        required=False, allow_null=True, default=None
    )


class TodoUpdateSerializer(TodoCreateSerializer):
    title = serializers.CharField(max_length=255, required=False)


class TodoPreferenceSerializer(ListMixin, CodeSerializer):
    category = serializers.CharField(read_only=True)
    category_label = serializers.SerializerMethodField()
    is_enabled = serializers.BooleanField(read_only=True)

    def get_category_label(self, obj: TodoPreference) -> str:
        return TodoReminderCategory(obj.category).label

    class Meta(CodeSerializer.Meta):
        model = TodoPreference
        fields = ["code", "category", "category_label", "is_enabled"]


class TodoPreferenceUpdateSerializer(WriteMixin, serializers.Serializer):
    is_enabled = serializers.BooleanField(required=True)
