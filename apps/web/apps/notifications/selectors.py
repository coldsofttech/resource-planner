from django.db.models import QuerySet

from apps.notifications.models import Notification, NotificationPreference
from apps.users.models import User


def get_notifications_queryset(user: User) -> QuerySet[Notification]:
    return Notification.objects.filter(user=user).select_related(
        "user", "created_by", "updated_by"
    )


def get_notification_by_code(user: User, code: str) -> Notification | None:
    try:
        return get_notifications_queryset(user).get(code=code)
    except Notification.DoesNotExist:
        return None


def get_unread_count(user: User) -> int:
    return (
        get_notifications_queryset(user)
        .filter(is_read=False, is_dismissed=False)
        .count()
    )


def get_preferences_for_user(user: User) -> QuerySet[NotificationPreference]:
    return NotificationPreference.objects.filter(user=user).order_by("category")


def get_preference(user: User, category: str) -> NotificationPreference | None:
    try:
        return NotificationPreference.objects.get(user=user, category=category)
    except NotificationPreference.DoesNotExist:
        return None
