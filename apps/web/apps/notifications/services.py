from __future__ import annotations

from typing import List

from django.db import transaction

from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService, FilterableQueryService, QueryService
from apps.notifications import selectors
from apps.notifications.constants import (
    NON_SUPPRESSIBLE_CATEGORIES,
    SUPPRESSIBLE_CATEGORIES,
    NotificationCategory,
)
from apps.notifications.models import Notification, NotificationPreference
from apps.users.models import User


class NotificationService(AuditableService, FilterableQueryService):
    _MODULE = "notifications"
    _RESOURCE_TYPE = "notification"

    filterable_fields: dict[str, str] = {
        "category": "category",
        "notification_type": "notification_type",
    }
    search_fields: list[str] = ["title", "body"]
    sortable_fields: list[str] = ["created_at", "is_read"]
    default_ordering: list[str] = ["-created_at"]

    def get_queryset(self):
        return selectors.get_notifications_queryset(self.user)

    def apply_filters(self, qs, filters: dict):
        qs = super().apply_filters(qs, filters)

        is_read_raw = filters.get("is_read")
        if is_read_raw not in (None, ""):
            qs = qs.filter(is_read=str(is_read_raw).lower() in ("true", "1"))

        is_dismissed_raw = filters.get("is_dismissed")
        if is_dismissed_raw in (None, ""):
            qs = qs.filter(is_dismissed=False)
        elif str(is_dismissed_raw).lower() != "all":
            qs = qs.filter(is_dismissed=str(is_dismissed_raw).lower() in ("true", "1"))

        return qs

    def get(self, code: str, *args, **kwargs) -> Notification:
        obj = selectors.get_notification_by_code(self.user, code)
        if obj is None:
            raise NotFoundException(
                resource="Notification", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        user: User,
        title: str,
        body: str,
        category: str = "general",
        notification_type: str = "info",
        link: str = "",
        force: bool = False,
    ) -> Notification | None:
        if not force and category not in NON_SUPPRESSIBLE_CATEGORIES:
            pref = selectors.get_preference(user, category)
            if pref is not None and not pref.is_enabled:
                return None

        return Notification.objects.create(
            user=user,
            title=title,
            body=body,
            link=link,
            category=category,
            notification_type=notification_type,
            created_by=self.user,
            updated_by=self.user,
        )

    @transaction.atomic
    def mark_read(self, code: str) -> Notification:
        notification = self.get(code=code)
        if not notification.is_read:
            notification.is_read = True
            notification.updated_by = self.user
            notification.save(update_fields=["is_read", "updated_by", "updated_at"])
        return notification

    @transaction.atomic
    def mark_unread(self, code: str) -> Notification:
        notification = self.get(code=code)
        if notification.is_read:
            notification.is_read = False
            notification.updated_by = self.user
            notification.save(update_fields=["is_read", "updated_by", "updated_at"])
        return notification

    @transaction.atomic
    def mark_all_read(self) -> int:
        qs = selectors.get_notifications_queryset(self.user).filter(is_read=False)
        return qs.update(is_read=True, updated_by=self.user)

    @transaction.atomic
    def dismiss(self, code: str) -> Notification:
        notification = self.get(code=code)
        if not notification.is_dismissed:
            notification.is_dismissed = True
            notification.updated_by = self.user
            notification.save(
                update_fields=["is_dismissed", "updated_by", "updated_at"]
            )
        return notification

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        notification = self.get(code=code)
        notification.delete()

    def unread_count(self) -> int:
        return selectors.get_unread_count(self.user)


class NotificationPreferenceService(AuditableService, QueryService):
    _MODULE = "notifications"
    _RESOURCE_TYPE = "notification_preference"

    def list(self, params=None, **kwargs) -> List[NotificationPreference]:
        return self.list_with_defaults()

    def get(self, category: str, *args, **kwargs) -> NotificationPreference:
        pref = selectors.get_preference(self.user, category)
        if pref is None:
            raise NotFoundException(
                resource="Notification preference",
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
        for category in SUPPRESSIBLE_CATEGORIES:
            if category not in existing:
                # CodeModel.code is set inside save(); bulk_create would skip it.
                NotificationPreference.objects.create(
                    user=self.user,
                    category=category,
                    is_enabled=True,
                    created_by=self.user,
                    updated_by=self.user,
                )

    def list_with_defaults(self) -> List[NotificationPreference]:
        # Non-suppressible categories have no DB row; represent them as unsaved,
        # always-enabled instances so the UI can list every category.
        self.ensure_defaults()
        persisted = list(selectors.get_preferences_for_user(self.user))
        virtual = [
            NotificationPreference(user=self.user, category=category, is_enabled=True)
            for category in NON_SUPPRESSIBLE_CATEGORIES
        ]
        return sorted(persisted + virtual, key=lambda pref: pref.category)

    @transaction.atomic
    def update_preference(
        self, category: str, is_enabled: bool
    ) -> NotificationPreference:
        if category not in NotificationCategory.values:
            raise ValidationException(f"Unknown notification category '{category}'.")

        if category in NON_SUPPRESSIBLE_CATEGORIES:
            raise ValidationException(
                f"Notifications in the '{category}' category cannot be suppressed."
            )

        pref, created = NotificationPreference.objects.get_or_create(
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
