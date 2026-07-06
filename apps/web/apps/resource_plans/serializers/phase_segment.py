from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin
from apps.resource_plans.constants import Progression, SegmentType


class PlanPhaseSegmentSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    segment_order = serializers.IntegerField(read_only=True)
    segment_type = serializers.CharField(read_only=True)
    segment_type_display = serializers.SerializerMethodField()
    start_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    end_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    progression = serializers.CharField(read_only=True)
    progression_display = serializers.SerializerMethodField()
    duration = serializers.IntegerField(read_only=True)
    step_count = serializers.IntegerField(read_only=True, allow_null=True)

    def get_segment_type_display(self, obj) -> str:
        return obj.get_segment_type_display()

    def get_progression_display(self, obj) -> str:
        return obj.get_progression_display()


class PlanPhaseSegmentCreateSerializer(WriteMixin, serializers.Serializer):
    segment_type = serializers.ChoiceField(choices=SegmentType.choices, required=True)
    start_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=True, min_value=0, max_value=100
    )
    end_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=True, min_value=0, max_value=100
    )
    progression = serializers.ChoiceField(
        choices=Progression.choices, required=False, default=Progression.LINEAR
    )
    duration = serializers.IntegerField(required=True, min_value=1)
    step_count = serializers.IntegerField(
        required=False, allow_null=True, default=None, min_value=1
    )
