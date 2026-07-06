from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.core.exceptions import ValidationException
from apps.core.services import AuditableService
from apps.resource_plans.constants import (
    CONFLICT_RESOLUTION_OPTIONS,
    ConflictResolutionType,
    ConflictStatus,
)
from apps.resource_plans.models import Conflict
from apps.resource_plans.services.manpower_request import ManpowerRequestService


class ConflictResolutionService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "conflict"

    def _snapshot(self, obj: Conflict) -> dict:
        return {
            "status": obj.status,
            "resolution_type": obj.resolution_type,
            "resolution_notes": obj.resolution_notes,
            "resolved_at": obj.resolved_at.isoformat() if obj.resolved_at else None,
        }

    @transaction.atomic
    def resolve(
        self,
        conflict: Conflict,
        resolution_type: str,
        notes: str = "",
        extra_data: dict | None = None,
    ) -> Conflict:
        allowed = CONFLICT_RESOLUTION_OPTIONS.get(conflict.conflict_type, ())
        if resolution_type not in allowed:
            raise ValidationException(
                f"'{resolution_type}' is not a valid resolution for "
                f"{conflict.get_conflict_type_display()} conflicts."
            )

        before = self._snapshot(conflict)

        conflict.resolution_type = resolution_type
        conflict.resolution_notes = notes
        conflict.resolved_at = timezone.now()
        conflict.status = (
            ConflictStatus.DISMISSED
            if resolution_type == ConflictResolutionType.DISMISSED
            else ConflictStatus.RESOLVED
        )
        update_fields = ["resolution_type", "resolution_notes", "resolved_at", "status"]
        if extra_data:
            conflict.engine_data = {**conflict.engine_data, **extra_data}
            update_fields.append("engine_data")
        conflict.save(update_fields=update_fields)

        if resolution_type == ConflictResolutionType.MANPOWER_RAISED:
            ManpowerRequestService(user=self.user).create_from_conflict(conflict)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=conflict.code,
            before=before,
            after=self._snapshot(conflict),
            actor=self.user,
        )
        return conflict
