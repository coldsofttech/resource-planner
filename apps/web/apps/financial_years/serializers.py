from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.financial_years.constants import FinancialYearStatus
from apps.financial_years.engine import FinancialYearEngine
from apps.financial_years.models import FinancialYear


class FinancialYearListSerializer(ListMixin, CodeSerializer):
    long_fy = serializers.CharField(read_only=True)
    short_fy = serializers.CharField(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    span_days = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_in_progress = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    in_threshold = serializers.SerializerMethodField()
    note = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_is_in_progress(self, obj: FinancialYear) -> bool:
        return obj.status == FinancialYearStatus.IN_PROGRESS

    def get_days_remaining(self, obj: FinancialYear) -> int:
        return FinancialYearEngine.days_remaining(obj.end_date)

    def get_in_threshold(self, obj: FinancialYear) -> bool:
        return FinancialYearEngine.in_threshold(obj.end_date)

    class Meta(CodeSerializer.Meta):
        model = FinancialYear
        fields = [
            "code",
            "long_fy",
            "short_fy",
            "start_date",
            "end_date",
            "span_days",
            "status",
            "is_active",
            "is_in_progress",
            "days_remaining",
            "in_threshold",
            "note",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class FinancialYearDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    long_fy = serializers.CharField(read_only=True)
    short_fy = serializers.CharField(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    span_days = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_remaining = serializers.SerializerMethodField()
    in_threshold = serializers.SerializerMethodField()
    note = serializers.CharField(read_only=True)

    def get_days_remaining(self, obj: FinancialYear) -> int:
        return FinancialYearEngine.days_remaining(obj.end_date)

    def get_in_threshold(self, obj: FinancialYear) -> bool:
        return FinancialYearEngine.in_threshold(obj.end_date)

    class Meta(AuditableSerializer.Meta):
        model = FinancialYear
        fields = [
            "code",
            "long_fy",
            "short_fy",
            "start_date",
            "end_date",
            "span_days",
            "status",
            "is_active",
            "days_remaining",
            "in_threshold",
            "note",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


_STATUS_CHOICES = [s[0] for s in FinancialYearStatus.CHOICES]


class FinancialYearCreateSerializer(WriteMixin, serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    status = serializers.ChoiceField(
        choices=_STATUS_CHOICES, default=FinancialYearStatus.FUTURE, required=False
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


class FinancialYearUpdateSerializer(WriteMixin, serializers.Serializer):
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
