from decimal import Decimal

from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint


class ProjectSprintActual(CodeModel, AuditableModel):
    MODEL_CODE = "PROJSAC"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="sprint_actuals",
        db_index=True,
    )
    sprint = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.CASCADE,
        related_name="project_actuals",
        db_index=True,
    )
    label = models.ForeignKey(
        "projects.ProjectLabel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sprint_actuals",
        db_index=True,
    )
    project_code = models.ForeignKey(
        "projects.ProjectCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sprint_actuals",
        db_index=True,
    )
    total_days = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )
    total_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )

    class Meta:
        ordering = ["project", "sprint", "label"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectsprintactual",
                fields=["project", "sprint", "label"],
            )
        ]
