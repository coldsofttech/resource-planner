from django.db import models

from apps.core.models import CodeModel, CreatedAtModel

from ..constants import OnboardingContactRole


class OnboardingContact(CodeModel, CreatedAtModel):
    MODEL_CODE = "PROJONBCT"

    role = models.CharField(
        max_length=50,
        choices=OnboardingContactRole.choices,
        db_index=True,
    )
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name or self.email

    def save(self, *args, **kwargs):
        if not self.name and self.email:
            local_part = self.email.split("@")[0]
            self.name = local_part.replace(".", " ").replace("_", " ").title()
        super().save(*args, **kwargs)
