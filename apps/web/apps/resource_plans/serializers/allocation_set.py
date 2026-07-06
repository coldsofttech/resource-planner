from rest_framework import serializers

from apps.core.serializers import ReadMixin


class AllocationSetSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    version_number = serializers.SerializerMethodField()
    engine_job_code = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    activated_at = serializers.DateTimeField(read_only=True, allow_null=True)
    notes = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_version_number(self, obj) -> int:
        return obj.version.version

    def get_engine_job_code(self, obj) -> str:
        return obj.engine_job.code

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()
