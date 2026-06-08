from __future__ import annotations

from django.db import models

from apps.audit.constants import Action
from apps.users.models import User


class Audit(models.Model):
    module = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_code = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )
    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["module", "resource_type"]),
            models.Index(fields=["module", "action"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.action} {self.resource_type} {self.resource_code} @{self.timestamp}"
        )
