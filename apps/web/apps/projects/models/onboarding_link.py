from django.db import models

from apps.core.models import CodeModel, CreatedAtModel

from .onboarding import Onboarding


class OnboardingLink(CodeModel, CreatedAtModel):
    MODEL_CODE = "PROJONBLNK"

    onboarding = models.ForeignKey(
        Onboarding,
        on_delete=models.CASCADE,
        related_name="links",
        db_index=True,
    )
    url = models.URLField(max_length=500)
    title = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["title", "url"]

    def __str__(self) -> str:
        return self.title or self.url
