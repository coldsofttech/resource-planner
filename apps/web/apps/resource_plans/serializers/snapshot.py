from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin


class SnapshotSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    notes = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    total_allocation_days = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    total_members = serializers.IntegerField(read_only=True)
    total_projects = serializers.IntegerField(read_only=True)
    total_sprints = serializers.IntegerField(read_only=True)
    initiated_at = serializers.DateTimeField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    duration_milliseconds = serializers.IntegerField(read_only=True, allow_null=True)
    error_log = serializers.JSONField(read_only=True)

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()


class SnapshotCreateSerializer(WriteMixin, serializers.Serializer):
    label = serializers.CharField(required=True, max_length=255)
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )


class SnapshotAllocationSerializer(ReadMixin, serializers.Serializer):
    sprint_number = serializers.IntegerField(read_only=True)
    sprint_name = serializers.CharField(read_only=True)
    member_name = serializers.CharField(read_only=True)
    team_name = serializers.CharField(read_only=True)
    project_name = serializers.CharField(read_only=True)
    programme_name = serializers.CharField(read_only=True)
    phase_name = serializers.CharField(read_only=True)
    assignment_type = serializers.CharField(read_only=True)
    assignment_type_display = serializers.SerializerMethodField()
    includes_in_budget = serializers.BooleanField(read_only=True)
    days = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_override = serializers.BooleanField(read_only=True)
    is_placeholder = serializers.BooleanField(read_only=True)

    def get_assignment_type_display(self, obj) -> str:
        return obj.get_assignment_type_display()
