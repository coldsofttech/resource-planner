from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.models import MemberCapacity, PlanVersion
from apps.sprints import selectors as sprint_selectors
from apps.teams import selectors as team_selectors


class CapacitySnapshotService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "member_capacity"

    def sync_for_version(self, version: PlanVersion) -> int:
        fy = version.plan.financial_year
        sprints = list(sprint_selectors.get_sprints_for_fy(fy.code))

        teams = selectors.get_teams_for_version(version)
        member_ids: set[int] = set()
        for team in teams:
            member_ids.update(
                team_selectors.get_active_members_for_team(team).values_list(
                    "id", flat=True
                )
            )

        placeholder_map: dict[tuple[int, int], Decimal] = {
            (pl.member_id, pl.sprint_id): pl.days
            for pl in selectors.get_placeholder_leaves_for_version(version)
        }

        now = timezone.now()
        new_rows = []
        if member_ids:
            for sprint in sprints:
                capacities = sprint_selectors.get_capacity_for_sprint(sprint).filter(
                    member_id__in=member_ids
                )
                for capacity in capacities:
                    placeholder_days = placeholder_map.get(
                        (capacity.member_id, sprint.id), Decimal("0")
                    )
                    net = max(capacity.net_capacity - placeholder_days, Decimal("0"))
                    new_rows.append(
                        MemberCapacity(
                            version=version,
                            member_id=capacity.member_id,
                            sprint=sprint,
                            working_days=capacity.working_days,
                            holiday_days=capacity.holiday_days,
                            leave_days=capacity.leave_days,
                            placeholder_leave_days=placeholder_days,
                            net_capacity=net,
                            synced_at=now,
                        )
                    )

        with transaction.atomic():
            MemberCapacity.objects.filter(version=version).delete()
            created = MemberCapacity.objects.bulk_create(new_rows)
        return len(created)

    def sync_record(
        self, version: PlanVersion, member_id: int, sprint_id: int
    ) -> MemberCapacity | None:
        capacity = sprint_selectors.get_capacity_by_ids(member_id, sprint_id)
        if capacity is None:
            MemberCapacity.objects.filter(
                version=version, member_id=member_id, sprint_id=sprint_id
            ).delete()
            return None

        placeholder = selectors.get_placeholder_leave_for_slot(
            version, member_id, sprint_id
        )
        placeholder_days = placeholder.days if placeholder else Decimal("0")
        net = max(capacity.net_capacity - placeholder_days, Decimal("0"))

        obj, _ = MemberCapacity.objects.update_or_create(
            version=version,
            member_id=member_id,
            sprint_id=sprint_id,
            defaults={
                "working_days": capacity.working_days,
                "holiday_days": capacity.holiday_days,
                "leave_days": capacity.leave_days,
                "placeholder_leave_days": placeholder_days,
                "net_capacity": net,
                "synced_at": timezone.now(),
            },
        )
        return obj
