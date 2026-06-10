from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.leaves.constants import HalfDayPeriod
from apps.leaves.models import Leave
from apps.users.models import User


class MemberBriefSerializer(serializers.Serializer):
    code = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    email = serializers.EmailField(read_only=True)

    def get_code(self, obj: User):
        try:
            return obj.profile.code
        except Exception:
            return None

    def get_display_name(self, obj: User):
        try:
            return obj.profile.display_name or obj.get_full_name() or obj.email
        except Exception:
            return obj.email


class LeaveListSerializer(ListMixin, CodeSerializer):
    member = MemberBriefSerializer(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    is_half_day = serializers.BooleanField(read_only=True)
    half_day_period = serializers.CharField(read_only=True, allow_null=True)
    half_day_period_display = serializers.SerializerMethodField()
    days = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=1)
    note = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_half_day_period_display(self, obj: Leave):
        if obj.half_day_period:
            try:
                return HalfDayPeriod(obj.half_day_period).label
            except ValueError:
                return obj.half_day_period
        return None

    class Meta(CodeSerializer.Meta):
        model = Leave
        fields = [
            "code",
            "member",
            "start_date",
            "end_date",
            "is_half_day",
            "half_day_period",
            "half_day_period_display",
            "days",
            "note",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class LeaveDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    member = MemberBriefSerializer(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    is_half_day = serializers.BooleanField(read_only=True)
    half_day_period = serializers.CharField(read_only=True, allow_null=True)
    half_day_period_display = serializers.SerializerMethodField()
    days = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=1)
    note = serializers.CharField(read_only=True)

    def get_half_day_period_display(self, obj: Leave):
        if obj.half_day_period:
            try:
                return HalfDayPeriod(obj.half_day_period).label
            except ValueError:
                return obj.half_day_period
        return None

    class Meta(AuditableSerializer.Meta):
        model = Leave
        fields = [
            "code",
            "member",
            "start_date",
            "end_date",
            "is_half_day",
            "half_day_period",
            "half_day_period_display",
            "days",
            "note",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class LeaveCreateSerializer(WriteMixin, serializers.Serializer):
    member_code = serializers.CharField(max_length=50, required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    is_half_day = serializers.BooleanField(required=False, default=False)
    half_day_period = serializers.ChoiceField(
        choices=HalfDayPeriod.choices,
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")


class LeaveUpdateSerializer(WriteMixin, serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    is_half_day = serializers.BooleanField(required=False)
    half_day_period = serializers.ChoiceField(
        choices=HalfDayPeriod.choices,
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    note = serializers.CharField(required=False, allow_blank=True)
