from django.db import models


class TodoStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    DONE = "done", "Done"


class TodoPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class TodoRecurrenceRule(models.TextChoices):
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"
    YEARLY = "yearly", "Yearly"


class TodoSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    MENTION = "mention", "Mention"


class TodoReminderCategory(models.TextChoices):
    DUE_REMINDER = "due_reminder", "Due date reminders"
    DAILY_DIGEST = "daily_digest", "Daily digest email"


# All to-do reminder categories are user-suppressible (opt-out via preferences).
SUPPRESSIBLE_REMINDER_CATEGORIES = tuple(TodoReminderCategory.values)

# Marker that flags a mention as an actionable item rather than a plain @mention.
TODO_MENTION_MARKER = "#todo"
