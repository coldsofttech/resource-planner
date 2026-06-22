from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import CodeModel
from apps.sprints.models.sprint_data_import import SprintDataImport


class SprintDataImportReview(CodeModel):
    MODEL_CODE = "SPTIRW"

    import_record = models.ForeignKey(
        SprintDataImport,
        on_delete=models.CASCADE,
        related_name="reviews",
        db_index=True,
    )
    reviewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sprint_import_reviews",
    )

    class Meta:
        ordering = ["-reviewed_at"]

    def __str__(self) -> str:
        return f"{self.code} — import {self.import_record_id}"
