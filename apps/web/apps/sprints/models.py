from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    unique_constraint,
)
from apps.financial_years.models import FinancialYear
from apps.sprints.constants import SprintStatus
from apps.users.models import User


class Sprint(CodeModel, AuditableModel, ActivatableModel):
    MODEL_CODE = "SPRINT"

    financial_year = models.ForeignKey(
        FinancialYear,
        on_delete=models.PROTECT,
        related_name="sprints",
        db_index=True,
    )
    sprint_number = models.PositiveIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    month = models.CharField(max_length=7, editable=False, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=SprintStatus.CHOICES,
        default=SprintStatus.FUTURE,
        db_index=True,
    )
    is_overridden = models.BooleanField(default=False, db_index=True)
    note = models.TextField(blank=True, default="")
    is_closed = models.BooleanField(default=False, db_index=True)
    closed_on = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="closed_sprint_set",
    )

    class Meta:
        ordering = ["sprint_number"]
        permissions = [
            ("import_sprint", "Can import sprints"),
            ("export_sprint", "Can export sprints"),
            ("generate_sprint", "Can generate sprints for a financial year"),
            ("close_sprint", "Can close/lock sprints"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs) -> None:
        if self.end_date:
            self.month = self.end_date.strftime("%Y-%m")
        super().save(*args, **kwargs)


class Capacity(AuditableModel):
    sprint = models.ForeignKey(
        Sprint,
        on_delete=models.CASCADE,
        related_name="capacities",
        db_index=True,
    )
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sprint_capacities",
        db_index=True,
    )
    working_days = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    holiday_days = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    leave_days = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    net_capacity = models.DecimalField(max_digits=6, decimal_places=1, default=0)

    class Meta:
        ordering = ["sprint", "member"]
        constraints = [
            unique_constraint(
                app_label="sprints",
                model="capacity",
                fields=["sprint", "member"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.member} — {self.sprint} capacity"
