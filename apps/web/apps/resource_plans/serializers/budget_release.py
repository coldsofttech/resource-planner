import re

from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin
from apps.resource_plans.constants import BudgetReleaseEntryType

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MONTH_FORMAT_ERROR = "Month must be in YYYY-MM format."


class PlanBudgetReleaseSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    entry_type = serializers.CharField(read_only=True)
    entry_type_display = serializers.SerializerMethodField()
    sprint_code = serializers.SerializerMethodField()
    sprint_name = serializers.SerializerMethodField()
    month = serializers.CharField(read_only=True, allow_null=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    notes = serializers.CharField(read_only=True)

    def get_entry_type_display(self, obj) -> str:
        return obj.get_entry_type_display()

    def get_sprint_code(self, obj) -> str | None:
        return obj.sprint.code if obj.sprint_id else None

    def get_sprint_name(self, obj) -> str | None:
        return obj.sprint.name if obj.sprint_id else None


class PlanBudgetReleaseCreateSerializer(WriteMixin, serializers.Serializer):
    entry_type = serializers.ChoiceField(
        choices=BudgetReleaseEntryType.choices, required=True
    )
    sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    month = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=True, min_value=0
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )

    def validate(self, attrs):
        if attrs.get("entry_type") == BudgetReleaseEntryType.SPRINT:
            if not attrs.get("sprint_code"):
                raise serializers.ValidationError(
                    {"sprint_code": "A sprint is required."}
                )
        else:
            month = attrs.get("month")
            if not month:
                raise serializers.ValidationError({"month": "A month is required."})
            if not MONTH_PATTERN.match(month):
                raise serializers.ValidationError({"month": MONTH_FORMAT_ERROR})
        return attrs


class PlanBudgetReleaseUpdateSerializer(WriteMixin, serializers.Serializer):
    sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    month = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=True, min_value=0
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )

    def validate(self, attrs):
        month = attrs.get("month")
        if month and not MONTH_PATTERN.match(month):
            raise serializers.ValidationError({"month": MONTH_FORMAT_ERROR})
        return attrs
