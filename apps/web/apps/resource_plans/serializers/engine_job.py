from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin
from apps.resource_plans.constants import EngineJobMode


class EngineJobStepSerializer(ReadMixin, serializers.Serializer):
    name = serializers.CharField(read_only=True)
    name_display = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    duration_milliseconds = serializers.IntegerField(read_only=True, allow_null=True)

    def get_name_display(self, obj) -> str:
        return obj.get_name_display()


class EngineJobSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    version_number = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    mode = serializers.CharField(read_only=True)
    mode_display = serializers.SerializerMethodField()
    current_step = serializers.CharField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    include_current_sprint = serializers.BooleanField(read_only=True)
    dry_run = serializers.BooleanField(read_only=True)
    initiated_at = serializers.DateTimeField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    duration_milliseconds = serializers.IntegerField(read_only=True, allow_null=True)
    validation_result = serializers.JSONField(read_only=True)
    error_log = serializers.JSONField(read_only=True)
    steps = EngineJobStepSerializer(many=True, read_only=True)

    def get_version_number(self, obj) -> int:
        return obj.version.version

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()

    def get_mode_display(self, obj) -> str:
        return obj.get_mode_display()


class EngineJobCreateSerializer(WriteMixin, serializers.Serializer):
    mode = serializers.ChoiceField(choices=EngineJobMode.choices, required=True)
    include_current_sprint = serializers.BooleanField(required=False, default=False)
