from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from apps.core.models import AuditableModel, CodeModel

User = get_user_model()


class UserProfile(AuditableModel, CodeModel):
    MODEL_CODE = "USER"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )

    class Meta:
        ordering = ["user"]
