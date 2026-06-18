from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.users.models import User

from .project import Project


class ProjectFollower(CodeModel, AuditableModel):
    MODEL_CODE = "PROJFLW"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="followers",
        db_index=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followed_projects",
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectfollower",
                fields=["project", "user"],
            )
        ]
