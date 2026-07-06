from decimal import Decimal

from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin


class AllocationSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    sprint_code = serializers.SerializerMethodField()
    engine_days = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    override_days = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, allow_null=True
    )
    override_notes = serializers.CharField(read_only=True)
    overridden_at = serializers.DateTimeField(read_only=True, allow_null=True)
    effective_days = serializers.SerializerMethodField()

    def get_sprint_code(self, obj) -> str:
        return obj.sprint.code

    def get_effective_days(self, obj) -> str:
        return str(Decimal(obj.effective_days).quantize(Decimal("0.01")))


class AllocationOverrideSerializer(WriteMixin, serializers.Serializer):
    override_days = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        allow_null=True,
        min_value=0,
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )
