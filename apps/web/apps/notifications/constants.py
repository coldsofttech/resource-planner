from django.db import models


class NotificationCategory(models.TextChoices):
    GENERAL = "general", "General"
    MENTION = "mention", "Mention"
    TODO = "todo", "To-do"


class NotificationType(models.TextChoices):
    INFO = "info", "Info"
    ERROR = "error", "Error"
    WARNING = "warning", "Warning"
    SUCCESS = "success", "Success"
    COMMENT = "comment", "Comment"
    REMINDER = "reminder", "Reminder"
