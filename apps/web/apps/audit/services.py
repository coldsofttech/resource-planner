from __future__ import annotations

from apps.audit.constants import Action
from apps.audit.models import Audit


class AuditService:
    """Static service for recording immutable audit log entries.

    Called from other services — does not need user/request context since
    actor is passed explicitly at the call site.
    """

    @staticmethod
    def log(
        *,
        module: str,
        resource_type: str,
        resource_code: str | None = None,
        action: str,
        before: dict | None = None,
        after: dict | None = None,
        actor=None,
    ) -> Audit:
        return Audit.objects.create(
            module=module,
            resource_type=resource_type,
            resource_code=resource_code,
            action=action,
            before=before,
            after=after,
            actor=actor,
        )

    @staticmethod
    def log_create(
        *,
        module: str,
        resource_type: str,
        resource_code: str | None = None,
        after: dict,
        actor=None,
    ) -> Audit:
        return AuditService.log(
            module=module,
            resource_type=resource_type,
            resource_code=resource_code,
            action=Action.CREATE,  # type: ignore[arg-type]
            before=None,
            after=after,
            actor=actor,
        )

    @staticmethod
    def log_update(
        *,
        module: str,
        resource_type: str,
        resource_code: str | None = None,
        before: dict,
        after: dict,
        actor=None,
    ) -> Audit:
        return AuditService.log(
            module=module,
            resource_type=resource_type,
            resource_code=resource_code,
            action=Action.UPDATE,  # type: ignore[arg-type]
            before=before,
            after=after,
            actor=actor,
        )

    @staticmethod
    def log_delete(
        *,
        module: str,
        resource_type: str,
        resource_code: str | None = None,
        before: dict,
        actor=None,
    ) -> Audit:
        return AuditService.log(
            module=module,
            resource_type=resource_type,
            resource_code=resource_code,
            action=Action.DELETE,  # type: ignore[arg-type]
            before=before,
            after=None,
            actor=actor,
        )

    @staticmethod
    def log_activate(
        *,
        module: str,
        resource_type: str,
        resource_code: str | None = None,
        before: dict | None = None,
        after: dict,
        actor=None,
    ) -> Audit:
        return AuditService.log(
            module=module,
            resource_type=resource_type,
            resource_code=resource_code,
            action=Action.ACTIVATE,  # type: ignore[arg-type]
            before=before,
            after=after,
            actor=actor,
        )

    @staticmethod
    def log_deactivate(
        *,
        module: str,
        resource_type: str,
        resource_code: str | None = None,
        before: dict,
        after: dict | None = None,
        actor=None,
    ) -> Audit:
        return AuditService.log(
            module=module,
            resource_type=resource_type,
            resource_code=resource_code,
            action=Action.DEACTIVATE,  # type: ignore[arg-type]
            before=before,
            after=after,
            actor=actor,
        )

    @staticmethod
    def log_set_default(
        *,
        module: str,
        resource_type: str,
        resource_code: str | None = None,
        before: dict,
        after: dict,
        actor=None,
    ) -> Audit:
        return AuditService.log(
            module=module,
            resource_type=resource_type,
            resource_code=resource_code,
            action=Action.SET_DEFAULT,  # type: ignore[arg-type]
            before=before,
            after=after,
            actor=actor,
        )
