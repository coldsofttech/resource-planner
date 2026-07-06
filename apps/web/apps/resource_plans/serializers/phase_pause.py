from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin
from apps.resource_plans.constants import PauseInputMode


class PlanPhasePauseSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    pause_from_code = serializers.SerializerMethodField()
    pause_from_name = serializers.SerializerMethodField()
    input_mode = serializers.CharField(read_only=True)
    input_mode_display = serializers.SerializerMethodField()
    pause_until_sprint_code = serializers.SerializerMethodField()
    pause_until_sprint_name = serializers.SerializerMethodField()
    pause_sprint_count = serializers.IntegerField(read_only=True, allow_null=True)
    resume_sprint_code = serializers.SerializerMethodField()
    resume_sprint_name = serializers.SerializerMethodField()
    notes = serializers.CharField(read_only=True)

    def get_pause_from_code(self, obj) -> str:
        return obj.pause_from.code

    def get_pause_from_name(self, obj) -> str:
        return obj.pause_from.name

    def get_input_mode_display(self, obj) -> str:
        return obj.get_input_mode_display()

    def get_pause_until_sprint_code(self, obj) -> str | None:
        return obj.pause_until_sprint.code if obj.pause_until_sprint_id else None

    def get_pause_until_sprint_name(self, obj) -> str | None:
        return obj.pause_until_sprint.name if obj.pause_until_sprint_id else None

    def get_resume_sprint_code(self, obj) -> str:
        return obj.resume_sprint.code

    def get_resume_sprint_name(self, obj) -> str:
        return obj.resume_sprint.name


class PlanPhasePauseCreateSerializer(WriteMixin, serializers.Serializer):
    pause_from_code = serializers.CharField(required=True)
    input_mode = serializers.ChoiceField(choices=PauseInputMode.choices, required=True)
    pause_until_sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    pause_sprint_count = serializers.IntegerField(
        required=False, allow_null=True, default=None, min_value=1
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )

    def validate(self, attrs):
        if attrs.get("input_mode") == PauseInputMode.SPRINT and not attrs.get(
            "pause_until_sprint_code"
        ):
            raise serializers.ValidationError(
                {"pause_until_sprint_code": "A pause-until sprint must be selected."}
            )
        if attrs.get("input_mode") == PauseInputMode.COUNT and attrs.get(
            "pause_sprint_count"
        ) in (None, ""):
            raise serializers.ValidationError(
                {"pause_sprint_count": "A pause sprint count is required."}
            )
        return attrs


class PlanPhasePauseUpdateSerializer(WriteMixin, serializers.Serializer):
    pause_from_code = serializers.CharField(required=True)
    input_mode = serializers.ChoiceField(choices=PauseInputMode.choices, required=True)
    pause_until_sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    pause_sprint_count = serializers.IntegerField(
        required=False, allow_null=True, default=None, min_value=1
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )

    def validate(self, attrs):
        if attrs.get("input_mode") == PauseInputMode.SPRINT and not attrs.get(
            "pause_until_sprint_code"
        ):
            raise serializers.ValidationError(
                {"pause_until_sprint_code": "A pause-until sprint must be selected."}
            )
        if attrs.get("input_mode") == PauseInputMode.COUNT and attrs.get(
            "pause_sprint_count"
        ) in (None, ""):
            raise serializers.ValidationError(
                {"pause_sprint_count": "A pause sprint count is required."}
            )
        return attrs
