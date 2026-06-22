from django.db import models

from apps.core.models import (
    AuditableModel,
    CodeModel,
    CreatedAtModel,
    unique_constraint,
)
from apps.users.models import User


class Comment(CodeModel, AuditableModel):
    MODEL_CODE = "COMMENT"

    comment = models.TextField()
    is_edited = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.comment[:72]


class CommentMention(CreatedAtModel):
    comment = models.ForeignKey(
        Comment, related_name="mentions", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_mentions"
    )

    class Meta:
        constraints = [
            unique_constraint(
                app_label="comments",
                model="commentmention",
                fields=["comment", "user"],
            )
        ]

    def __str__(self):
        return f"{self.user} on {self.comment_id}"
