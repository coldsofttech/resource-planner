from rest_framework import serializers

from apps.core.serializers import ReadMixin, WriteMixin
from apps.resource_plans.constants import AssignmentType


class PlanAssignmentSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    member_code = serializers.SerializerMethodField()
    member_name = serializers.SerializerMethodField()
    auto_assign = serializers.BooleanField(read_only=True)
    assignment_type = serializers.CharField(read_only=True)
    assignment_type_display = serializers.SerializerMethodField()
    replaces_member_code = serializers.SerializerMethodField()
    replaces_member_name = serializers.SerializerMethodField()
    interim_sprint_count = serializers.IntegerField(read_only=True, allow_null=True)
    split_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, allow_null=True
    )
    includes_in_budget = serializers.BooleanField(read_only=True)
    notes = serializers.CharField(read_only=True)

    def get_member_code(self, obj) -> str:
        return obj.member.profile.code

    def get_member_name(self, obj) -> str:
        return obj.member.profile.display_name

    def get_assignment_type_display(self, obj) -> str:
        return obj.get_assignment_type_display()

    def get_replaces_member_code(self, obj) -> str | None:
        return obj.replaces_member.profile.code if obj.replaces_member_id else None

    def get_replaces_member_name(self, obj) -> str | None:
        return (
            obj.replaces_member.profile.display_name if obj.replaces_member_id else None
        )


class PlanAssignmentCreateSerializer(WriteMixin, serializers.Serializer):
    member_code = serializers.CharField(required=True)
    auto_assign = serializers.BooleanField(required=False, default=False)
    assignment_type = serializers.ChoiceField(
        choices=AssignmentType.choices, required=True
    )
    replaces_member_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    interim_sprint_count = serializers.IntegerField(
        required=False, allow_null=True, default=None, min_value=1
    )
    split_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        min_value=0,
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )

    def validate(self, attrs):
        if attrs.get("assignment_type") == AssignmentType.INTERIM:
            if not attrs.get("replaces_member_code"):
                raise serializers.ValidationError(
                    {"replaces_member_code": "A member to replace must be selected."}
                )
            if attrs.get("interim_sprint_count") in (None, ""):
                raise serializers.ValidationError(
                    {"interim_sprint_count": "An interim sprint count is required."}
                )
        return attrs


class PlanAssignmentUpdateSerializer(WriteMixin, serializers.Serializer):
    member_code = serializers.CharField(required=True)
    auto_assign = serializers.BooleanField(required=False, default=False)
    assignment_type = serializers.ChoiceField(
        choices=AssignmentType.choices, required=True
    )
    replaces_member_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    interim_sprint_count = serializers.IntegerField(
        required=False, allow_null=True, default=None, min_value=1
    )
    split_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        min_value=0,
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )

    def validate(self, attrs):
        if attrs.get("assignment_type") == AssignmentType.INTERIM:
            if not attrs.get("replaces_member_code"):
                raise serializers.ValidationError(
                    {"replaces_member_code": "A member to replace must be selected."}
                )
            if attrs.get("interim_sprint_count") in (None, ""):
                raise serializers.ValidationError(
                    {"interim_sprint_count": "An interim sprint count is required."}
                )
        return attrs
