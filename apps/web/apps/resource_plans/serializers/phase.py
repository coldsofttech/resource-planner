from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin
from apps.resource_plans.constants import RampPattern, SplitMode


class PlanPhaseSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    sequence_order = serializers.IntegerField(read_only=True)
    start_sprint_code = serializers.SerializerMethodField()
    start_sprint_name = serializers.SerializerMethodField()
    end_sprint_code = serializers.SerializerMethodField()
    end_sprint_name = serializers.SerializerMethodField()
    max_days_per_sprint = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, allow_null=True
    )
    ramp_pattern = serializers.CharField(read_only=True)
    ramp_pattern_display = serializers.SerializerMethodField()
    allow_multiple_engineers = serializers.BooleanField(read_only=True)
    split_mode = serializers.CharField(read_only=True)
    split_mode_display = serializers.SerializerMethodField()
    is_split_incomplete = serializers.BooleanField(read_only=True)
    notes = serializers.CharField(read_only=True)
    days_effort = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    def get_start_sprint_code(self, obj) -> str | None:
        return obj.start_sprint.code if obj.start_sprint_id else None

    def get_start_sprint_name(self, obj) -> str | None:
        return obj.start_sprint.name if obj.start_sprint_id else None

    def get_end_sprint_code(self, obj) -> str | None:
        return obj.end_sprint.code if obj.end_sprint_id else None

    def get_end_sprint_name(self, obj) -> str | None:
        return obj.end_sprint.name if obj.end_sprint_id else None

    def get_ramp_pattern_display(self, obj) -> str:
        return obj.get_ramp_pattern_display()

    def get_split_mode_display(self, obj) -> str:
        return obj.get_split_mode_display()


class PlanPhaseCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(required=True, max_length=255)
    sequence_order = serializers.IntegerField(required=False, default=1, min_value=1)
    start_sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    end_sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    max_days_per_sprint = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        min_value=0,
    )
    ramp_pattern = serializers.ChoiceField(
        choices=RampPattern.choices, required=False, default=RampPattern.FLAT
    )
    allow_multiple_engineers = serializers.BooleanField(required=False, default=False)
    split_mode = serializers.ChoiceField(
        choices=SplitMode.choices, required=False, default=SplitMode.AUTO
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )


class PlanPhaseUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(required=True, max_length=255)
    sequence_order = serializers.IntegerField(required=False, default=1, min_value=1)
    start_sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    end_sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    max_days_per_sprint = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        min_value=0,
    )
    ramp_pattern = serializers.ChoiceField(
        choices=RampPattern.choices, required=False, default=RampPattern.FLAT
    )
    allow_multiple_engineers = serializers.BooleanField(required=False, default=False)
    split_mode = serializers.ChoiceField(
        choices=SplitMode.choices, required=False, default=SplitMode.AUTO
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )
