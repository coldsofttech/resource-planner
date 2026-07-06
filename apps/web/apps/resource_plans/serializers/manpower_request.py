from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin
from apps.resource_plans.constants import ManpowerRequestStatus


class ManpowerRequestSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    team_code = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    phase_code = serializers.SerializerMethodField()
    phase_name = serializers.SerializerMethodField()
    conflict_code = serializers.SerializerMethodField()
    sprints_needed = serializers.IntegerField(read_only=True)
    days_needed = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    is_finalized = serializers.SerializerMethodField()
    resolution_notes = serializers.CharField(read_only=True)
    resolved_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_team_code(self, obj) -> str:
        return obj.team.code

    def get_team_name(self, obj) -> str:
        return obj.team.name

    def get_phase_code(self, obj) -> str | None:
        return obj.phase.code if obj.phase_id else None

    def get_phase_name(self, obj) -> str | None:
        return obj.phase.name if obj.phase_id else None

    def get_conflict_code(self, obj) -> str:
        return obj.conflict.code

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()

    def get_is_finalized(self, obj) -> bool:
        return obj.status != ManpowerRequestStatus.OPEN


class ManpowerRequestHireSerializer(WriteMixin, serializers.Serializer):
    onboard_sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )


class ManpowerRequestActionSerializer(WriteMixin, serializers.Serializer):
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )


class EngineerHirePlaceholderSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    sequence_number = serializers.IntegerField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    team_code = serializers.SerializerMethodField()
    onboard_sprint_code = serializers.SerializerMethodField()
    engine_suggested_sprint_code = serializers.SerializerMethodField()

    def get_team_code(self, obj) -> str:
        return obj.team.code

    def get_onboard_sprint_code(self, obj) -> str | None:
        return obj.onboard_sprint.code if obj.onboard_sprint_id else None

    def get_engine_suggested_sprint_code(self, obj) -> str | None:
        return (
            obj.engine_suggested_sprint.code if obj.engine_suggested_sprint_id else None
        )
