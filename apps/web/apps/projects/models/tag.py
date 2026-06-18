from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.tags.models import Tag

from .project import Project


class ProjectTag(CodeModel, AuditableModel):
    MODEL_CODE = "PROJTAG"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tags",
        db_index=True,
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="project_tags",
        db_index=True,
    )

    class Meta:
        ordering = ["tag__name"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projecttag",
                fields=["project", "tag"],
            )
        ]
