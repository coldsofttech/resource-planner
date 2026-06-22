from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import CreatedAtModel
from apps.sprints.constants import ImportRowCheckStatus
from apps.sprints.models.sprint_data_import_review import SprintDataImportReview


class SprintDataImportReviewCapacityResult(CreatedAtModel):
    review = models.ForeignKey(
        SprintDataImportReview,
        on_delete=models.CASCADE,
        related_name="capacity_results",
        db_index=True,
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sprint_import_capacity_results",
        db_index=True,
    )
    allocated_days = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    net_capacity = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    status = models.CharField(
        max_length=10,
        choices=ImportRowCheckStatus.CHOICES,
        db_index=True,
    )

    class Meta:
        unique_together = [["review", "member"]]
        ordering = ["member__first_name", "member__last_name"]

    def __str__(self) -> str:
        return f"Capacity check: {self.member_id} — {self.status}"
