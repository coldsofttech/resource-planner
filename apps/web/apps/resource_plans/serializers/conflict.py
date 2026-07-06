from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin
from apps.resource_plans.constants import (
    CONFLICT_RESOLUTION_OPTIONS,
    ConflictResolutionType,
    ConflictStatus,
)


class ConflictSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    conflict_type = serializers.CharField(read_only=True)
    conflict_type_display = serializers.SerializerMethodField()
    severity = serializers.IntegerField(read_only=True)
    severity_display = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    is_finalized = serializers.SerializerMethodField()
    affected_project_code = serializers.SerializerMethodField()
    affected_project_name = serializers.SerializerMethodField()
    affected_phase_code = serializers.SerializerMethodField()
    affected_phase_name = serializers.SerializerMethodField()
    affected_member_code = serializers.SerializerMethodField()
    affected_member_name = serializers.SerializerMethodField()
    affected_sprint_code = serializers.SerializerMethodField()
    affected_sprint_name = serializers.SerializerMethodField()
    affected_team_code = serializers.SerializerMethodField()
    affected_team_name = serializers.SerializerMethodField()
    description = serializers.CharField(read_only=True)
    resolution_type = serializers.CharField(read_only=True, allow_null=True)
    resolution_type_display = serializers.SerializerMethodField()
    resolution_notes = serializers.CharField(read_only=True)
    resolved_at = serializers.DateTimeField(read_only=True, allow_null=True)
    allowed_resolutions = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    def get_conflict_type_display(self, obj) -> str:
        return obj.get_conflict_type_display()

    def get_severity_display(self, obj) -> str:
        return obj.get_severity_display()

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()

    def get_is_finalized(self, obj) -> bool:
        return obj.status != ConflictStatus.OPEN

    def get_affected_project_code(self, obj) -> str | None:
        return obj.affected_project.code if obj.affected_project_id else None

    def get_affected_project_name(self, obj) -> str | None:
        return obj.affected_project.name if obj.affected_project_id else None

    def get_affected_phase_code(self, obj) -> str | None:
        return obj.affected_phase.code if obj.affected_phase_id else None

    def get_affected_phase_name(self, obj) -> str | None:
        return obj.affected_phase.name if obj.affected_phase_id else None

    def get_affected_member_code(self, obj) -> str | None:
        return obj.affected_member.profile.code if obj.affected_member_id else None

    def get_affected_member_name(self, obj) -> str | None:
        return (
            obj.affected_member.profile.display_name if obj.affected_member_id else None
        )

    def get_affected_sprint_code(self, obj) -> str | None:
        return obj.affected_sprint.code if obj.affected_sprint_id else None

    def get_affected_sprint_name(self, obj) -> str | None:
        return obj.affected_sprint.name if obj.affected_sprint_id else None

    def get_affected_team_code(self, obj) -> str | None:
        return obj.affected_team.code if obj.affected_team_id else None

    def get_affected_team_name(self, obj) -> str | None:
        return obj.affected_team.name if obj.affected_team_id else None

    def get_resolution_type_display(self, obj) -> str | None:
        return obj.get_resolution_type_display() if obj.resolution_type else None

    def get_allowed_resolutions(self, obj) -> list[dict]:
        allowed = CONFLICT_RESOLUTION_OPTIONS.get(obj.conflict_type, ())
        labels = dict(ConflictResolutionType.choices)
        return [
            {"value": value, "label": labels.get(value, value)} for value in allowed
        ]


class ConflictResolveSerializer(WriteMixin, serializers.Serializer):
    resolution_type = serializers.ChoiceField(
        choices=ConflictResolutionType.choices, required=True
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )
    extra_data = serializers.JSONField(required=False, allow_null=True, default=None)
