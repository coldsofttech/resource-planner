from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint

from .project import Project


class ProjectAttachment(CodeModel, AuditableModel):
    MODEL_CODE = "PROJAT"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="attachments",
        db_index=True,
    )
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True, default="")
    file_size = models.PositiveIntegerField(default=0)
    file_path = models.TextField()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectattachment",
                fields=["project", "file_name"],
            )
        ]
