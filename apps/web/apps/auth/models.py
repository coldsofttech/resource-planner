import secrets

from django.db import models

from apps.core.models import TimeStampedModel
from apps.users.models import User

RESET_CODE_EXPIRY_MINUTES = 10


class PasswordResetToken(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    email = models.EmailField(db_index=True)
    token_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class AdminPasswordResetToken(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_password_reset_tokens",
    )
    token_hash = models.CharField(max_length=64, db_index=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class UserToken(TimeStampedModel):
    user = models.ForeignKey(
        User,
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


class PasswordHistory(TimeStampedModel):
    """Stores retired password hashes so PASSWORD_HISTORY_COUNT can block reuse."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_history",
    )
    password_hash = models.CharField(max_length=128)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Password histories"
