from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.sprints.constants import SprintStatus
from apps.sprints.engine import SprintEngine
from apps.sprints.models import Sprint


class FinancialYearMiniSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    long_fy = serializers.CharField(read_only=True)
    short_fy = serializers.CharField(read_only=True)


class SprintListSerializer(ListMixin, CodeSerializer):
    sprint_number = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    financial_year = FinancialYearMiniSerializer(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    month = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_overridden = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    is_in_progress = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    note = serializers.CharField(read_only=True)
    closed_on = serializers.DateTimeField(read_only=True, allow_null=True)
    closed_by = UserMiniSerializer(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_is_in_progress(self, obj: Sprint) -> bool:
        return obj.status == SprintStatus.IN_PROGRESS

    def get_days_remaining(self, obj: Sprint) -> int:
        return SprintEngine.days_remaining(obj.end_date)

    class Meta(CodeSerializer.Meta):
        model = Sprint
        fields = [
            "code",
            "sprint_number",
            "name",
            "financial_year",
            "start_date",
            "end_date",
            "month",
            "status",
            "is_active",
            "is_overridden",
            "is_closed",
            "is_in_progress",
            "days_remaining",
            "note",
            "closed_on",
            "closed_by",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class SprintDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    sprint_number = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    financial_year = FinancialYearMiniSerializer(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    month = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_overridden = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    is_in_progress = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    note = serializers.CharField(read_only=True)
    closed_on = serializers.DateTimeField(read_only=True, allow_null=True)
    closed_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_is_in_progress(self, obj: Sprint) -> bool:
        return obj.status == SprintStatus.IN_PROGRESS

    def get_days_remaining(self, obj: Sprint) -> int:
        return SprintEngine.days_remaining(obj.end_date)

    class Meta(AuditableSerializer.Meta):
        model = Sprint
        fields = [
            "code",
            "sprint_number",
            "name",
            "financial_year",
            "start_date",
            "end_date",
            "month",
            "status",
            "is_active",
            "is_overridden",
            "is_closed",
            "is_in_progress",
            "days_remaining",
            "note",
            "closed_on",
            "closed_by",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


_STATUS_CHOICES = [s[0] for s in SprintStatus.CHOICES]


class SprintCreateSerializer(WriteMixin, serializers.Serializer):
    fy_code = serializers.CharField(required=True)
    sprint_number = serializers.IntegerField(required=True, min_value=1)
    name = serializers.CharField(required=False, allow_blank=True, default="")
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    status = serializers.ChoiceField(
        choices=_STATUS_CHOICES, default=SprintStatus.FUTURE, required=False
    )
    note = serializers.CharField(allow_blank=True, default="", required=False)
    is_active = serializers.BooleanField(default=True, required=False)

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )
        return attrs


class SprintUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    status = serializers.ChoiceField(choices=_STATUS_CHOICES, required=False)
    note = serializers.CharField(allow_blank=True, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )
        return attrs


class SprintGenerateSerializer(WriteMixin, serializers.Serializer):
    fy_code = serializers.CharField(required=True)


class SprintCloseSerializer(WriteMixin, serializers.Serializer):
    lock = serializers.BooleanField(default=True, required=False)
