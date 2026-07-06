from django.db import models

from apps.comments.models import Comment
from apps.core.models import AuditableModel, CodeModel

from .plan import Plan


class PlanComment(CodeModel, AuditableModel):
    MODEL_CODE = "RESCOMMENT"

    class Meta(CodeModel.Meta, AuditableModel.Meta):
        pass

    plan = models.ForeignKey(
        Plan,
        related_name="plan_comments",
        on_delete=models.CASCADE,
        db_index=True,
    )
    comment = models.OneToOneField(
        Comment, related_name="resource_plan_link", on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f"{self.plan} / {self.comment_id}"
