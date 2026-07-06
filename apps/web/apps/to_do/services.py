from __future__ import annotations

import calendar
from datetime import date as date_cls
from datetime import timedelta
from typing import List

from django.db import transaction
from django.utils import timezone
from django.utils.html import strip_tags

from apps.comments.models import Comment
from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService, FilterableQueryService, QueryService
from apps.notifications.constants import NotificationCategory
from apps.notifications.services import NotificationService
from apps.to_do import selectors
from apps.to_do.constants import (
    SUPPRESSIBLE_REMINDER_CATEGORIES,
    TodoPriority,
    TodoRecurrenceRule,
    TodoReminderCategory,
    TodoSource,
    TodoStatus,
)
from apps.to_do.models import Todo, TodoPreference
from apps.users.models import User

_UPDATABLE_FIELDS = [
    "title",
    "description",
    "priority",
    "group",
    "due_date",
    "reminder_at",
    "is_recurring",
    "recurrence_rule",
    "recurrence_interval",
    "recurrence_end_date",
]


class TodoService(AuditableService, FilterableQueryService):
    _MODULE = "to_do"
    _RESOURCE_TYPE = "todo"

    filterable_fields: dict[str, str] = {
        "priority": "priority",
        "group": "group",
    }
    search_fields: list[str] = ["title", "description"]
    sortable_fields: list[str] = ["due_date", "priority", "created_at", "status"]
    default_ordering: list[str] = ["status", "due_date", "-created_at"]

    def get_queryset(self):
        return selectors.get_todos_queryset(self.user)

    def apply_filters(self, qs, filters: dict):
        qs = super().apply_filters(qs, filters)

        status_raw = filters.get("status")
        if status_raw in (None, ""):
            qs = qs.exclude(status=TodoStatus.DONE)
        elif str(status_raw).lower() != "all":
            qs = qs.filter(status=status_raw)

        due_filter = filters.get("due_filter")
        today = timezone.localdate()
        if due_filter == "today":
            qs = qs.filter(due_date=today)
        elif due_filter == "overdue":
            qs = qs.filter(due_date__lt=today).exclude(status=TodoStatus.DONE)
        elif due_filter == "this_week":
            week_end = today + timedelta(days=(6 - today.weekday()))
            qs = qs.filter(due_date__gte=today, due_date__lte=week_end)

        return qs

    def get(self, code: str, *args, **kwargs) -> Todo:
        obj = selectors.get_todo_by_code(self.user, code)
        if obj is None:
            raise NotFoundException(
                resource="Todo", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        title: str,
        description: str = "",
        priority: str = "medium",
        group: str = "",
        due_date=None,
        reminder_at=None,
        is_recurring: bool = False,
        recurrence_rule: str = "",
        recurrence_interval: int = 1,
        recurrence_end_date=None,
    ) -> Todo:
        return Todo.objects.create(
            title=title,
            description=description,
            priority=priority,
            group=group,
            due_date=due_date,
            reminder_at=reminder_at,
            assigned_to=self.user,
            is_recurring=is_recurring,
            recurrence_rule=recurrence_rule,
            recurrence_interval=recurrence_interval,
            recurrence_end_date=recurrence_end_date,
            source=TodoSource.MANUAL,
            created_by=self.user,
            updated_by=self.user,
        )

    @transaction.atomic
    def update(self, *, code: str, **data) -> Todo:
        obj = self.get(code=code)

        update_fields = []
        for field in _UPDATABLE_FIELDS:
            if field in data:
                setattr(obj, field, data[field])
                update_fields.append(field)

        if "reminder_at" in data:
            obj.reminder_sent = False
            update_fields.append("reminder_sent")

        obj.updated_by = self.user
        update_fields += ["updated_by", "updated_at"]
        obj.save(update_fields=update_fields)
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        obj.delete()

    @transaction.atomic
    def complete(self, code: str) -> Todo:
        obj = self.get(code=code)
        if obj.status != TodoStatus.DONE:
            obj.status = TodoStatus.DONE
            obj.completed_at = timezone.now()
            obj.updated_by = self.user
            obj.save(
                update_fields=["status", "completed_at", "updated_by", "updated_at"]
            )
            if obj.is_recurring and obj.recurrence_rule:
                self._spawn_next_occurrence(obj)
        return obj

    @transaction.atomic
    def reopen(self, code: str) -> Todo:
        obj = self.get(code=code)
        if obj.status == TodoStatus.DONE:
            obj.status = TodoStatus.OPEN
            obj.completed_at = None
            obj.updated_by = self.user
            obj.save(
                update_fields=["status", "completed_at", "updated_by", "updated_at"]
            )
        return obj

    def open_count(self) -> int:
        return selectors.get_open_todos_count(self.user)

    @transaction.atomic
    def due_reminders(self) -> List[Todo]:
        """Return to-dos due for a reminder right now and mark them as sent.

        Intended to be polled while the user is logged in, so each due reminder
        is only ever surfaced once (poll-and-consume), independent of the
        not-yet-implemented daily digest email job.
        """
        pref = selectors.get_preference(self.user, "due_reminder")
        if pref is not None and not pref.is_enabled:
            return []

        todos = list(selectors.get_due_reminders_queryset(self.user))
        if todos:
            Todo.objects.filter(pk__in=[t.pk for t in todos]).update(reminder_sent=True)
        return todos

    def _actor_label(self) -> str:
        if self.user is None:
            return "Someone"
        return self.user.get_full_name() or getattr(self.user, "email", "") or "Someone"

    @transaction.atomic
    def create_from_mention(
        self,
        *,
        comment: Comment,
        mentioned_user: User,
        link: str,
        context_label: str,
    ) -> Todo:
        """Create an actionable to-do for a mentioned user from a '#todo' comment."""
        text = strip_tags(comment.comment).strip()
        title = text[:255] if text else f"Follow up on {context_label}"

        todo = Todo.objects.create(
            title=title,
            description=text,
            priority=TodoPriority.MEDIUM,
            assigned_to=mentioned_user,
            source=TodoSource.MENTION,
            source_comment=comment,
            created_by=self.user,
            updated_by=self.user,
        )

        NotificationService(user=self.user).create(
            user=mentioned_user,
            title=f"New to-do from {self._actor_label()}",
            body=title,
            category=NotificationCategory.TODO,
            link=link,
        )
        return todo

    def _spawn_next_occurrence(self, completed: Todo) -> None:
        rule = completed.recurrence_rule
        interval = completed.recurrence_interval or 1
        base_date = completed.due_date or timezone.localdate()

        if rule == TodoRecurrenceRule.DAILY:
            next_date = base_date + timedelta(days=interval)
        elif rule == TodoRecurrenceRule.WEEKLY:
            next_date = base_date + timedelta(weeks=interval)
        elif rule == TodoRecurrenceRule.MONTHLY:
            month = base_date.month - 1 + interval
            year = base_date.year + month // 12
            month = month % 12 + 1
            day = min(base_date.day, calendar.monthrange(year, month)[1])
            next_date = date_cls(year, month, day)
        elif rule == TodoRecurrenceRule.YEARLY:
            try:
                next_date = base_date.replace(year=base_date.year + interval)
            except ValueError:
                next_date = base_date.replace(year=base_date.year + interval, day=28)
        else:
            return

        if completed.recurrence_end_date and next_date > completed.recurrence_end_date:
            return

        root = completed.parent_todo or completed
        Todo.objects.create(
            title=completed.title,
            description=completed.description,
            priority=completed.priority,
            group=completed.group,
            due_date=next_date,
            assigned_to=completed.assigned_to,
            is_recurring=True,
            recurrence_rule=rule,
            recurrence_interval=interval,
            recurrence_end_date=completed.recurrence_end_date,
            parent_todo=root,
            source=completed.source,
            status=TodoStatus.OPEN,
            created_by=self.user,
            updated_by=self.user,
        )


class TodoPreferenceService(AuditableService, QueryService):
    _MODULE = "to_do"
    _RESOURCE_TYPE = "todo_preference"

    def list(self, params=None, **kwargs) -> List[TodoPreference]:
        return self.list_with_defaults()

    def get(self, category: str, *args, **kwargs) -> TodoPreference:
        pref = selectors.get_preference(self.user, category)
        if pref is None:
            raise NotFoundException(
                resource="Todo preference",
                lookup_field="category",
                lookup_value=category,
            )
        return pref

    def ensure_defaults(self) -> None:
        """Create default (enabled) rows for categories not yet configured."""
        existing = set(
            selectors.get_preferences_for_user(self.user).values_list(
                "category", flat=True
            )
        )
        for category in SUPPRESSIBLE_REMINDER_CATEGORIES:
            if category not in existing:
                # CodeModel.code is set inside save(); bulk_create would skip it.
                TodoPreference.objects.create(
                    user=self.user,
                    category=category,
                    is_enabled=True,
                    created_by=self.user,
                    updated_by=self.user,
                )

    def list_with_defaults(self) -> List[TodoPreference]:
        self.ensure_defaults()
        return list(selectors.get_preferences_for_user(self.user))

    @transaction.atomic
    def update_preference(self, category: str, is_enabled: bool) -> TodoPreference:
        if category not in TodoReminderCategory.values:
            raise ValidationException(f"Unknown to-do reminder category '{category}'.")

        pref, created = TodoPreference.objects.get_or_create(
            user=self.user,
            category=category,
            defaults={
                "is_enabled": is_enabled,
                "created_by": self.user,
                "updated_by": self.user,
            },
        )
        if not created and pref.is_enabled != is_enabled:
            pref.is_enabled = is_enabled
            pref.updated_by = self.user
            pref.save(update_fields=["is_enabled", "updated_by", "updated_at"])
        return pref
