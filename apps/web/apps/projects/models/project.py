from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    CreatedAtModel,
    DescriptionModel,
    NamedModel,
    unique_constraint,
)
from apps.projects.constants import Confidence, Priority
from apps.teams.models import Team

from .programme import Programme
from .project_status import ProjectStatus, ProjectSubStatus
from .project_type import ProjectType


class Project(
    CodeModel, NamedModel, DescriptionModel, ActivatableModel, AuditableModel
):
    MODEL_CODE = "PROJ"

    display_name = models.CharField(max_length=255, blank=True, db_index=True)
    project_type = models.ForeignKey(
        ProjectType,
        on_delete=models.PROTECT,
        related_name="projects",
        db_index=True,
    )
    programme = models.ForeignKey(
        Programme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        db_index=True,
    )
    status = models.ForeignKey(
        ProjectStatus,
        on_delete=models.PROTECT,
        related_name="projects",
        db_index=True,
    )
    sub_status = models.ForeignKey(
        ProjectSubStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        db_index=True,
    )
    assigned_team = models.ForeignKey(
        Team,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_projects",
        db_index=True,
    )
    efforts_issued = models.BooleanField(default=False, db_index=True)
    commitment_date = models.DateField(null=True, blank=True)
    run_cost_applies = models.BooleanField(default=False, db_index=True)
    confidence = models.CharField(
        max_length=20,
        choices=Confidence.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(app_label="projects", model="project", fields=["name"])
        ]
        permissions = [
            ("import_project", "Can import projects"),
            ("export_project", "Can export projects"),
        ]


class ProjectCollaborator(CreatedAtModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="collaborators",
        db_index=True,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="collaborating_projects",
        db_index=True,
    )
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["added_on"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectcollaborator",
                fields=["project", "team"],
            )
        ]
