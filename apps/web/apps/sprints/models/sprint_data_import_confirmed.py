from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import CreatedAtModel
from apps.sprints.models.sprint import Sprint
from apps.sprints.models.sprint_data_import import SprintDataImport
from apps.teams.models import Team


class SprintDataImportConfirmed(CreatedAtModel):
    sprint = models.ForeignKey(
        Sprint,
        on_delete=models.CASCADE,
        related_name="data_import_confirmed",
        db_index=True,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="sprint_data_import_confirmed",
        db_index=True,
    )
    import_record = models.ForeignKey(
        SprintDataImport,
        on_delete=models.CASCADE,
        related_name="confirmed_rows",
        db_index=True,
    )
    import_type = models.CharField(max_length=20, db_index=True)
    story_type = models.CharField(max_length=255, blank=True, default="")
    jira_id = models.CharField(max_length=255, blank=True, default="")
    title = models.CharField(max_length=500, blank=True, default="")
    assignee = models.CharField(max_length=255, blank=True, default="")
    efforts = models.CharField(max_length=100, blank=True, default="")
    days = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    label = models.CharField(max_length=255, blank=True, default="")
    mapping = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["pk"]

    def __str__(self) -> str:
        return f"{self.sprint} — {self.team} — {self.jira_id or self.pk}"
