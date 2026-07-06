from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.to_do.constants import TodoStatus
from apps.to_do.models import Todo, TodoPreference
from apps.users.models import User


def get_todos_queryset(user: User) -> QuerySet[Todo]:
    return Todo.objects.filter(Q(created_by=user) | Q(assigned_to=user)).select_related(
        "created_by", "updated_by", "assigned_to", "source_comment"
    )


def get_todo_by_code(user: User, code: str) -> Todo | None:
    try:
        return get_todos_queryset(user).get(code=code)
    except Todo.DoesNotExist:
        return None


def get_open_todos_count(user: User) -> int:
    return get_todos_queryset(user).exclude(status=TodoStatus.DONE).count()


def get_due_reminders_queryset(user: User) -> QuerySet[Todo]:
    now = timezone.now()
    return (
        get_todos_queryset(user)
        .filter(reminder_at__isnull=False, reminder_at__lte=now, reminder_sent=False)
        .exclude(status=TodoStatus.DONE)
    )


def get_preferences_for_user(user: User) -> QuerySet[TodoPreference]:
    return TodoPreference.objects.filter(user=user).order_by("category")


def get_preference(user: User, category: str) -> TodoPreference | None:
    try:
        return TodoPreference.objects.get(user=user, category=category)
    except TodoPreference.DoesNotExist:
        return None
