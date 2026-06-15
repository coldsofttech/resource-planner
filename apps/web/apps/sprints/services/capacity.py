from __future__ import annotations

from django.db import transaction

from apps.core.services import AuditableService
from apps.sprints import selectors


class CapacityService(AuditableService):
    _MODULE = "sprints"
    _RESOURCE_TYPE = "capacity"

    def get_for_sprint(self, sprint_code: str):
        from apps.sprints.services.sprint import SprintService

        sprint = SprintService(user=self.user).get(code=sprint_code)
        return selectors.get_capacity_for_sprint(sprint)

    @transaction.atomic
    def rebuild(self, sprint_code: str) -> int:
        from apps.sprints.engine import SprintCapacityEngine
        from apps.sprints.services.sprint import SprintService

        sprint = SprintService(user=self.user).get(code=sprint_code)
        return SprintCapacityEngine.rebuild_for_sprint(sprint, actor=self.user)
