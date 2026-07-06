from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin
from apps.resource_plans.constants import AllocationType


class PlanVersionTeamSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    team_code = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    allocation_type = serializers.CharField(read_only=True)
    allocation_type_display = serializers.SerializerMethodField()
    allocation_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True, allow_null=True
    )
    allocation_days = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, allow_null=True
    )
    allocation_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True, allow_null=True
    )
    allocated_days = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    sequence_order = serializers.IntegerField(read_only=True)

    def get_team_code(self, obj) -> str:
        return obj.team.code

    def get_team_name(self, obj) -> str:
        return obj.team.name

    def get_allocation_type_display(self, obj) -> str:
        return obj.get_allocation_type_display()


class PlanVersionTeamCreateSerializer(WriteMixin, serializers.Serializer):
    team_code = serializers.CharField(required=True)
    allocation_type = serializers.ChoiceField(
        choices=AllocationType.choices, required=True
    )
    value = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=True, min_value=0
    )
    sequence_order = serializers.IntegerField(required=False, default=1, min_value=1)

    def validate(self, attrs):
        if (
            attrs.get("allocation_type") == AllocationType.PERCENT
            and attrs.get("value") > 100
        ):
            raise serializers.ValidationError(
                {"value": "Percentage cannot exceed 100."}
            )
        return attrs


class PlanVersionTeamUpdateSerializer(WriteMixin, serializers.Serializer):
    allocation_type = serializers.ChoiceField(
        choices=AllocationType.choices, required=True
    )
    value = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=True, min_value=0
    )
    sequence_order = serializers.IntegerField(required=False, default=1, min_value=1)

    def validate(self, attrs):
        if (
            attrs.get("allocation_type") == AllocationType.PERCENT
            and attrs.get("value") > 100
        ):
            raise serializers.ValidationError(
                {"value": "Percentage cannot exceed 100."}
            )
        return attrs
