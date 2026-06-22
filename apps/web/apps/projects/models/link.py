from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint

from .project import Project


class ProjectLink(CodeModel, AuditableModel):
    MODEL_CODE = "PROJLNK"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="links",
        db_index=True,
    )
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=500)

    class Meta:
        ordering = ["title"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectlink",
                fields=["project", "title"],
            )
        ]
