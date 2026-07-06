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


# Categories the user cannot suppress via preferences (always delivered).
NON_SUPPRESSIBLE_CATEGORIES = frozenset(
    {NotificationCategory.MENTION, NotificationCategory.TODO}
)

# Categories the user can configure via NotificationPreference.
SUPPRESSIBLE_CATEGORIES = tuple(
    c for c in NotificationCategory.values if c not in NON_SUPPRESSIBLE_CATEGORIES
)
