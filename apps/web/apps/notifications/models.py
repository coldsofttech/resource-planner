from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.users.models import User

from .constants import NotificationCategory, NotificationType


class Notification(CodeModel, AuditableModel):
    MODEL_CODE = "NOTIF"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    link = models.URLField(blank=True, default="")
    category = models.CharField(
        max_length=20,
        choices=NotificationCategory.choices,
        default=NotificationCategory.GENERAL,
        db_index=True,
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        db_index=True,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    is_dismissed = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "is_dismissed"]),
        ]

    def __str__(self) -> str:
        return self.title


class NotificationPreference(CodeModel, AuditableModel):
    MODEL_CODE = "NOTIFPREF"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    category = models.CharField(
        max_length=20,
        choices=NotificationCategory.choices,
        db_index=True,
    )
    is_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["category"]
        constraints = [
            unique_constraint(
                app_label="notifications",
                model="notificationpreference",
                fields=["user", "category"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} - {self.category}"
