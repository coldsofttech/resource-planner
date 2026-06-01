import secrets

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel

RESET_CODE_EXPIRY_MINUTES = 10


class PasswordResetToken(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    email = models.EmailField(db_index=True)
    token_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class UserToken(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auth_tokens",
    )
    key = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def generate_key(cls) -> str:
        return secrets.token_urlsafe(48)
