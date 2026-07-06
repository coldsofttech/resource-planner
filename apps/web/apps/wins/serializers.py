from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator
from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.wins.models import MonthlyWin, MonthlyWinsRecipient, Win, WinEntry


class WinListSerializer(ListMixin, CodeSerializer):
    week_number = serializers.IntegerField(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    status = serializers.CharField(read_only=True)
    entries_count = serializers.SerializerMethodField()
    teams = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta(CodeSerializer.Meta):
        model = Win
        fields = [
            "code",
            "week_number",
            "start_date",
            "end_date",
            "status",
            "entries_count",
            "teams",
            "created_at",
        ]

    def get_entries_count(self, obj: Win) -> int:
        return len(obj.entries.all())

    def get_teams(self, obj: Win) -> list[str]:
        seen: list[str] = []
        for entry in obj.entries.all():
            name = entry.team.name
            if name not in seen:
                seen.append(name)
        return seen


class WinDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    week_number = serializers.IntegerField(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    status = serializers.CharField(read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    reviewed_by = serializers.SerializerMethodField()

    class Meta(AuditableSerializer.Meta):
        model = Win
        fields = [
            "code",
            "week_number",
            "start_date",
            "end_date",
            "status",
            "reviewed_at",
            "reviewed_by",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]

    def get_reviewed_by(self, obj: Win) -> dict | None:
        if obj.reviewed_by is None or obj.reviewed_by.user is None:
            return None
        return UserMiniSerializer(obj.reviewed_by.user).data


class WinCreateSerializer(WriteMixin, serializers.Serializer):
    start_date = serializers.DateField(required=True)


class WinEntryListSerializer(ListMixin, CodeSerializer):
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    team = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = WinEntry
        fields = [
            "code",
            "title",
            "description",
            "team",
            "created_at",
            "created_by",
        ]

    def get_team(self, obj: WinEntry) -> dict:
        return {"code": obj.team.code, "name": obj.team.name}


class WinEntryCreateSerializer(WriteMixin, serializers.Serializer):
    team = serializers.CharField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")


class WinEntryUpdateSerializer(WriteMixin, serializers.Serializer):
    team = serializers.CharField(required=False)
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class WinEntrySuggestSerializer(WriteMixin, serializers.Serializer):
    team_name = serializers.CharField(required=True)
    project_line = serializers.CharField(required=False, allow_blank=True, default="")
    delivered = serializers.CharField(required=False, allow_blank=True, default="")
    benefits = serializers.CharField(required=False, allow_blank=True, default="")
    next_steps = serializers.CharField(required=False, allow_blank=True, default="")


class MonthlyWinsRecipientListSerializer(ListMixin, CodeSerializer):
    team = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta(CodeSerializer.Meta):
        model = MonthlyWinsRecipient
        fields = ["code", "team", "user", "created_at"]

    def get_team(self, obj: MonthlyWinsRecipient) -> dict:
        return {"code": obj.team.code, "name": obj.team.name}

    def get_user(self, obj: MonthlyWinsRecipient) -> dict:
        return UserMiniSerializer(obj.user).data


class MonthlyWinsRecipientCreateSerializer(WriteMixin, serializers.Serializer):
    team = serializers.CharField(required=True)
    user = serializers.CharField(required=True, help_text="Member code, e.g. USER-5")


class MonthlyWinsRecipientUpdateSerializer(WriteMixin, serializers.Serializer):
    team = serializers.CharField(required=False)
    user = serializers.CharField(required=False, help_text="Member code, e.g. USER-5")


class MonthlyWinListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    phase1_deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    phase2_deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    weeks_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta(CodeSerializer.Meta):
        model = MonthlyWin
        fields = [
            "code",
            "name",
            "status",
            "phase1_deadline",
            "phase2_deadline",
            "weeks_count",
            "created_at",
        ]

    def get_weeks_count(self, obj: MonthlyWin) -> int:
        return len(obj.wins.all())


class MonthlyWinDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    phase1_deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    phase2_deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    weeks = serializers.SerializerMethodField()

    class Meta(AuditableSerializer.Meta):
        model = MonthlyWin
        fields = [
            "code",
            "name",
            "status",
            "phase1_deadline",
            "phase2_deadline",
            "weeks",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]

    def get_weeks(self, obj: MonthlyWin) -> list[dict]:
        return [
            {"code": w.code, "week_number": w.week_number}
            for w in obj.wins.order_by("week_number")
        ]


class MonthlyWinCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    win_codes = serializers.ListField(
        child=serializers.CharField(), required=True, allow_empty=False
    )
    phase1_deadline = serializers.DateTimeField(required=False, allow_null=True)


class MonthlyWinSurveyListSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    phase = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    recipient = serializers.SerializerMethodField()
    teams = serializers.SerializerMethodField()
    sent_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)

    def get_recipient(self, obj) -> dict:
        return UserMiniSerializer(obj.recipient).data

    def get_teams(self, obj) -> list[str]:
        return [t.name for t in obj.teams.all()]


class MonthlyWinNominationSubmitSerializer(WriteMixin, serializers.Serializer):
    entry_code = serializers.CharField(required=True)
    category = serializers.CharField(required=True)


class MonthlyWinSurveySubmitSerializer(WriteMixin, serializers.Serializer):
    nominations = MonthlyWinNominationSubmitSerializer(many=True, required=True)


class WinsConfigSerializer(serializers.Serializer):
    """Read serializer for Wins configuration."""

    win_start_number = serializers.IntegerField()
    wins_review_email_recipients = serializers.CharField(allow_blank=True)


class WinsConfigUpdateSerializer(serializers.Serializer):
    """Write serializer — accepts partial updates."""

    win_start_number = serializers.IntegerField(min_value=1, required=False)
    wins_review_email_recipients = serializers.CharField(
        allow_blank=True, required=False
    )

    def validate_wins_review_email_recipients(self, value: str) -> str:
        validator = EmailValidator()
        for addr in [a.strip() for a in value.split(",") if a.strip()]:
            try:
                validator(addr)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    f"'{addr}' is not a valid email address."
                ) from exc
        return value
