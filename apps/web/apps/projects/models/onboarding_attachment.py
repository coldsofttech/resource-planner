from django.db import models

from apps.core.models import CodeModel, CreatedAtModel

from .onboarding import Onboarding


class OnboardingAttachment(CodeModel, CreatedAtModel):
    MODEL_CODE = "PROJONBAT"

    onboarding = models.ForeignKey(
        Onboarding,
        on_delete=models.CASCADE,
        related_name="attachments",
        db_index=True,
    )
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, default="")
    file_size = models.PositiveIntegerField(default=0)
    file_path = models.TextField(default="")

    class Meta:
        ordering = ["file_name"]

    def __str__(self) -> str:
        return self.file_name
