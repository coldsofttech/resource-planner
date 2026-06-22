from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.sprints.constants import SprintDataImportStatus, SprintDataImportType
from apps.sprints.models.sprint import Sprint
from apps.teams.models import Team


class SprintDataImport(CodeModel, AuditableModel):
    MODEL_CODE = "SPTIMP"

    sprint = models.ForeignKey(
        Sprint,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="data_imports",
        db_index=True,
    )
    team = models.ForeignKey(
        Team,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sprint_data_imports",
        db_index=True,
    )
    version_number = models.PositiveIntegerField(db_index=True)
    file_name = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=SprintDataImportStatus.CHOICES,
        default=SprintDataImportStatus.ACTIVE,
        db_index=True,
    )
    import_type = models.CharField(
        max_length=20,
        choices=SprintDataImportType.CHOICES,
        default=SprintDataImportType.FORECAST,
        db_index=True,
    )

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            unique_constraint(
                app_label="sprints",
                model="sprintdataimport",
                fields=["sprint", "team", "import_type", "version_number"],
            ),
        ]
        permissions = [
            ("import_forecast", "Can upload forecast data for a sprint team"),
            ("import_actuals", "Can upload actuals data for a sprint team"),
            ("review_forecast", "Can run review checks on a forecast import"),
            ("confirm_forecast", "Can confirm a reviewed forecast import"),
        ]

    def __str__(self) -> str:
        return f"{self.team} — {self.sprint} {self.import_type} v{self.version_number}"
