from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.users.models import User

from .project import Project


class ProjectCode(CodeModel, AuditableModel):
    MODEL_CODE = "PROJCODE"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="codes",
        db_index=True,
    )
    value = models.CharField(max_length=255, db_index=True)
    note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectcode",
                fields=["project"],
            )
        ]


class ProjectCodeHistory(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="code_history",
        db_index=True,
    )
    previous_code = models.ForeignKey(
        ProjectCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_as_previous_code",
    )
    new_code = models.ForeignKey(
        ProjectCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_as_new_code",
    )
    note = models.TextField(blank=True, default="")
    changed_on = models.DateTimeField(auto_now_add=True, db_index=True)
    changed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_code_changes",
    )

    class Meta:
        ordering = ["-changed_on"]
