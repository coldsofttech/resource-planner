from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import unique_constraint
from apps.sprints.models.sprint import Sprint
from apps.sprints.models.sprint_data_import_review import SprintDataImportReview


class SprintDataImportReviewComplete(models.Model):
    sprint = models.ForeignKey(
        Sprint,
        on_delete=models.CASCADE,
        related_name="import_completions",
        db_index=True,
    )
    review = models.ForeignKey(
        SprintDataImportReview,
        on_delete=models.CASCADE,
        related_name="completions",
        db_index=True,
    )
    import_type = models.CharField(max_length=20, db_index=True)
    completed_at = models.DateTimeField(auto_now=True, db_index=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sprint_import_completions",
    )
    override_applied = models.BooleanField(default=False)
    override_notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-completed_at"]
        constraints = [
            unique_constraint(
                app_label="sprints",
                model="sprintdataimportreviewcomplete",
                fields=["sprint", "import_type"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sprint} — {self.import_type} completion"
