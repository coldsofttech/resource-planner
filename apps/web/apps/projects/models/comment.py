from django.db import models

from apps.comments.models import Comment
from apps.core.models import AuditableModel, CodeModel

from .project import Project


class ProjectComment(CodeModel, AuditableModel):
    MODEL_CODE = "PROJCOMMENT"

    class Meta(CodeModel.Meta, AuditableModel.Meta):
        pass

    project = models.ForeignKey(
        Project,
        related_name="project_comments",
        on_delete=models.CASCADE,
        db_index=True,
    )
    comment = models.OneToOneField(
        Comment, related_name="project_link", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.project} / {self.comment_id}"
