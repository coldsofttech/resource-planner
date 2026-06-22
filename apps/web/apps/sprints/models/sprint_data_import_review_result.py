from __future__ import annotations

from django.db import models

from apps.core.models import CreatedAtModel
from apps.sprints.constants import ImportRowCheck, ImportRowCheckStatus
from apps.sprints.models.sprint_data_import_review import SprintDataImportReview


class SprintDataImportReviewResult(CreatedAtModel):
    review = models.ForeignKey(
        SprintDataImportReview,
        on_delete=models.CASCADE,
        related_name="results",
        db_index=True,
    )
    row = models.ForeignKey(
        "sprints.SprintDataImportRow",
        on_delete=models.CASCADE,
        related_name="review_results",
        db_index=True,
    )
    check_type = models.CharField(
        max_length=30,
        choices=ImportRowCheck.CHOICES,
        db_index=True,
    )
    status = models.CharField(
        max_length=10,
        choices=ImportRowCheckStatus.CHOICES,
        db_index=True,
    )
    message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["check_type"]

    def __str__(self) -> str:
        return f"{self.check_type}: {self.status}"
