from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.configurations.selectors import Sprint as SprintConfig
from apps.core.services import AuditableService
from apps.resource_plans.models import (
    EngineerHirePlaceholder,
    EngineerHirePlaceholderAbsence,
)
from apps.sprints import selectors as sprint_selectors


class PlaceholderEngineerAbsenceService(AuditableService):
    """Backs the absence-forecast side of the hire-placeholder workflow — a
    hire placeholder has no real leave history yet, so absences are a flat
    per-sprint assumption from DEFAULT_HOLIDAYS_PER_SPRINT until the person
    actually joins.
    """

    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "engineer_hire_placeholder_absence"

    @transaction.atomic
    def generate_absences(self, hire_placeholder: EngineerHirePlaceholder) -> int:
        """(Re)generates absence rows from onboard_sprint onward within the plan's
        financial year. Idempotent — existing rows for sprints still in scope are
        left untouched (preserving any override_days/override_notes); rows for
        sprints that fell out of scope (e.g. onboard_sprint moved later) are
        removed.
        """
        if hire_placeholder.onboard_sprint_id is None:
            hire_placeholder.absences.all().delete()
            return 0

        fy = hire_placeholder.version.plan.financial_year
        sprints = list(
            sprint_selectors.get_sprints_for_fy(fy.code).filter(
                sprint_number__gte=hire_placeholder.onboard_sprint.sprint_number
            )
        )
        sprint_ids = {s.id for s in sprints}

        hire_placeholder.absences.exclude(sprint_id__in=sprint_ids).delete()
        existing_sprint_ids = set(
            hire_placeholder.absences.values_list("sprint_id", flat=True)
        )

        default_days = Decimal(str(SprintConfig.get_default_holidays_per_sprint()))
        created = 0
        for sprint in sprints:
            if sprint.id in existing_sprint_ids:
                continue
            EngineerHirePlaceholderAbsence.objects.create(
                placeholder_engineer=hire_placeholder,
                sprint=sprint,
                days=default_days,
                is_engine_generated=True,
            )
            created += 1
        return created

    def override_absence(
        self,
        absence: EngineerHirePlaceholderAbsence,
        override_days: Decimal | None,
        notes: str = "",
    ) -> EngineerHirePlaceholderAbsence:
        # A no-op override (equal to the original days) is cleared rather than
        # stored, so it doesn't linger as a false "this was overridden" signal.
        if override_days is not None and override_days == absence.days:
            override_days = None

        absence.override_days = override_days
        absence.override_notes = notes if override_days is not None else ""
        absence.save(update_fields=["override_days", "override_notes"])
        return absence
