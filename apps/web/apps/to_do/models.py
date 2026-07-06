from django.db import models

from apps.comments.models import Comment
from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.users.models import User

from .constants import (
    TodoPriority,
    TodoRecurrenceRule,
    TodoReminderCategory,
    TodoSource,
    TodoStatus,
)


class Todo(CodeModel, AuditableModel):
    MODEL_CODE = "TODO"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=TodoStatus.choices,
        default=TodoStatus.OPEN,
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=TodoPriority.choices,
        default=TodoPriority.MEDIUM,
        db_index=True,
    )
    group = models.CharField(max_length=100, blank=True, default="", db_index=True)

    due_date = models.DateField(null=True, blank=True, db_index=True)
    reminder_at = models.DateTimeField(null=True, blank=True, db_index=True)
    reminder_sent = models.BooleanField(default=False)

    assigned_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="todos_assigned",
    )

    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(
        max_length=10, choices=TodoRecurrenceRule.choices, blank=True, default=""
    )
    recurrence_interval = models.PositiveIntegerField(default=1)
    recurrence_end_date = models.DateField(null=True, blank=True)
    parent_todo = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recurrence_children",
    )

    source = models.CharField(
        max_length=10, choices=TodoSource.choices, default=TodoSource.MANUAL
    )
    source_comment = models.ForeignKey(
        Comment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_todos",
    )

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["status", "due_date", "-created_at"]
        indexes = [
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["reminder_at", "reminder_sent"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def is_overdue(self) -> bool:
        if self.status == TodoStatus.DONE or not self.due_date:
            return False
        from datetime import date

        return self.due_date < date.today()


class TodoPreference(CodeModel, AuditableModel):
    MODEL_CODE = "TODOPREF"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="todo_preferences"
    )
    category = models.CharField(
        max_length=20,
        choices=TodoReminderCategory.choices,
        db_index=True,
    )
    is_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["category"]
        constraints = [
            unique_constraint(
                app_label="to_do",
                model="todopreference",
                fields=["user", "category"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} - {self.category}"
