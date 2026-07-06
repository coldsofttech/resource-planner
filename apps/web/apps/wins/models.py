import uuid

from django.db import models

from apps.core.models import (
    AuditableModel,
    CodeModel,
    DescriptionModel,
    TimeStampedModel,
    unique_constraint,
)
from apps.teams.models import Team
from apps.users.models import User, UserProfile
from apps.wins.constants import (
    MonthlyWinStatus,
    SurveyPhase,
    SurveyStatus,
    WinCategory,
    WinStatus,
)


class Win(CodeModel, AuditableModel):
    """A single Weekly Win week — the container for that week's WinEntry rows."""

    MODEL_CODE = "WIN"

    week_number = models.PositiveIntegerField(unique=True, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=WinStatus.choices, default=WinStatus.OPEN, db_index=True
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_wins",
    )

    class Meta:
        ordering = ["-week_number"]
        permissions = [
            ("review_complete_win", "Can mark a Weekly Win as review complete"),
        ]

    def __str__(self) -> str:
        return f"Week {self.week_number}"

    @property
    def date_range_label(self) -> str:
        start = self.start_date.strftime("%d %b %Y")
        end = self.end_date.strftime("%d %b %Y")
        return f"{start} – {end}"


class WinEntry(CodeModel, DescriptionModel, AuditableModel):
    """A single team's submission for a given Weekly Win week."""

    MODEL_CODE = "WINENT"

    win = models.ForeignKey(Win, on_delete=models.CASCADE, related_name="entries")
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="win_entries", db_index=True
    )
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.team} — {self.title}"


class MonthlyWinsRecipient(CodeModel, AuditableModel):
    """A user who receives Monthly Wins surveys on behalf of a team."""

    MODEL_CODE = "MWREC"

    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="monthly_wins_recipients"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="monthly_wins_recipient_of"
    )

    class Meta:
        ordering = ["team__name", "user__email"]
        constraints = [
            unique_constraint(
                app_label="wins",
                model="monthlywinsrecipient",
                fields=["team", "user"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.team}"


class MonthlyWin(CodeModel, AuditableModel):
    """A monthly nomination round spanning one or more Weekly Win weeks."""

    MODEL_CODE = "MWIN"

    name = models.CharField(max_length=255)
    wins = models.ManyToManyField(Win, related_name="monthly_wins", blank=True)
    status = models.CharField(
        max_length=20,
        choices=MonthlyWinStatus.choices,
        default=MonthlyWinStatus.DRAFT,
        db_index=True,
    )
    phase1_deadline = models.DateTimeField(null=True, blank=True)
    phase2_deadline = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("manage_monthlywin", "Can manage Monthly Win phases and surveys"),
        ]

    def __str__(self) -> str:
        return self.name


class MonthlyWinSurvey(CodeModel, TimeStampedModel):
    """A single recipient's nomination survey for one phase of a MonthlyWin."""

    MODEL_CODE = "MWSURV"

    monthly_win = models.ForeignKey(
        MonthlyWin, on_delete=models.CASCADE, related_name="surveys"
    )
    phase = models.CharField(max_length=10, choices=SurveyPhase.choices, db_index=True)
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="monthly_win_surveys"
    )
    teams = models.ManyToManyField(Team, blank=True, related_name="monthly_win_surveys")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(
        max_length=15,
        choices=SurveyStatus.choices,
        default=SurveyStatus.PENDING,
        db_index=True,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    reminder_count = models.PositiveIntegerField(default=0)
    last_reminder_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["recipient__email"]

    def __str__(self) -> str:
        return f"{self.monthly_win} / {self.phase} / {self.recipient}"


class MonthlyWinSurveyNomination(models.Model):
    """A recipient's vote for one WinEntry in one category, on one survey."""

    survey = models.ForeignKey(
        MonthlyWinSurvey, on_delete=models.CASCADE, related_name="nominations"
    )
    entry = models.ForeignKey(
        WinEntry, on_delete=models.CASCADE, related_name="nominations"
    )
    category = models.CharField(max_length=25, choices=WinCategory.choices)
    is_dismissed = models.BooleanField(default=False)
    dismissed_reason = models.CharField(max_length=300, blank=True)
    nominated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "entry__team__name"]
        constraints = [
            unique_constraint(
                app_label="wins",
                model="monthlywinsurveynomination",
                fields=["survey", "entry", "category"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.survey} / {self.category} / {self.entry_id}"


class MonthlyWinResult(models.Model):
    """The declared top-ranked WinEntry rows per category for a MonthlyWin."""

    monthly_win = models.ForeignKey(
        MonthlyWin, on_delete=models.CASCADE, related_name="results"
    )
    entry = models.ForeignKey(
        WinEntry, on_delete=models.CASCADE, related_name="monthly_results"
    )
    category = models.CharField(max_length=25, choices=WinCategory.choices)
    rank = models.PositiveIntegerField()
    vote_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "rank"]
        constraints = [
            unique_constraint(
                app_label="wins",
                model="monthlywinresult",
                fields=["monthly_win", "category", "rank"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.monthly_win} / {self.category} / #{self.rank}"
