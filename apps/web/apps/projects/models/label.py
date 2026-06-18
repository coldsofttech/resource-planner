from django.db import models

from apps.core.models import (
    AuditableModel,
    CodeModel,
    DefaultableModel,
    unique_constraint,
)

from .project import Project


class ProjectLabel(CodeModel, DefaultableModel, AuditableModel):
    MODEL_CODE = "PROJLBL"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="labels",
        db_index=True,
    )
    label = models.CharField(max_length=50, db_index=True)

    class Meta:
        ordering = ["-is_default", "label"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectlabel",
                fields=["project", "label"],
            )
        ]
        permissions = [
            ("import_projectlabel", "Can import project labels"),
            ("export_projectlabel", "Can export project labels"),
        ]
