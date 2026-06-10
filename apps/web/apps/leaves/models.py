from django.db import models
from django.db.models import F, Q

from apps.core.models import (
    AuditableModel,
    BaseModel,
    CodeModel,
    check_constraint,
    unique_constraint,
)
from apps.leaves.constants import HalfDayPeriod
from apps.users.models import User


class Leave(CodeModel, AuditableModel):
    MODEL_CODE = "LEAVE"

    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="leaves",
        db_index=True,
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    is_half_day = models.BooleanField(default=False, db_index=True)
    half_day_period = models.CharField(
        max_length=2,
        choices=HalfDayPeriod.choices,
        null=True,
        blank=True,
    )
    days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            check_constraint(
                app_label="leaves",
                model="leave",
                suffix="end_gte_start",
                condition=Q(end_date__gte=F("start_date")),
            ),
        ]
        permissions = [
            ("import_leave", "Can import leaves"),
            ("export_leave", "Can export leaves"),
        ]

    def __str__(self) -> str:
        return f"{self.code}: {self.member_id} {self.start_date}–{self.end_date}"


class LeaveDayEntry(BaseModel):
    """One row per working day counted against a Leave.

    Rows are deleted and recreated whenever the leave range or holiday calendar
    changes — `created_at` therefore records the last time this day was included
    in the calculation.
    """

    leave = models.ForeignKey(
        Leave,
        on_delete=models.CASCADE,
        related_name="day_entries",
        db_index=True,
    )
    date = models.DateField(db_index=True)
    is_half_day = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["date"]
        constraints = [
            unique_constraint(
                app_label="leaves",
                model="leavedayentry",
                fields=["leave", "date"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.leave_id} — {self.date}"
