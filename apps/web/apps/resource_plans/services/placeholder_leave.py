from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Q

from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException
from apps.core.services import AuditableService, paginate_queryset
from apps.core.types import ListParams, PaginatedResult
from apps.leaves import selectors as leave_selectors
from apps.resource_plans import selectors
from apps.resource_plans.models import PlaceholderLeave, Plan, PlanVersion
from apps.sprints import selectors as sprint_selectors
from apps.sprints.constants import SprintStatus
from apps.sprints.models import Sprint
from apps.teams import selectors as team_selectors
from apps.users import selectors as user_selectors
from apps.users.models import User


class PlaceholderLeaveService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "placeholder_leave"

    def _snapshot(self, obj: PlaceholderLeave) -> dict:
        return {
            "member_code": obj.member.profile.code,
            "sprint_code": obj.sprint.code,
            "days": float(obj.days),
            "is_auto": obj.is_auto,
            "notes": obj.notes,
        }

    def _resource_code(
        self, plan: Plan, version_number: int, obj: PlaceholderLeave
    ) -> str:
        return f"{plan.code}-v{version_number}-{obj.code}"

    def _get_plan(self, plan_code: str) -> Plan:
        obj = selectors.get_resource_plan_by_code(plan_code)
        if obj is None:
            raise NotFoundException(
                resource="Plan", lookup_field="code", lookup_value=plan_code
            )
        return obj

    def _get_version(self, plan_code: str, version: int) -> PlanVersion:
        plan = self._get_plan(plan_code)
        obj = selectors.get_version_by_number(plan, version)
        if obj is None:
            raise NotFoundException(
                resource="PlanVersion",
                lookup_field="version",
                lookup_value=version,
            )
        return obj

    def _get_placeholder_leave(
        self, *, plan_code: str, version: int, leave_code: str
    ) -> PlaceholderLeave:
        version_obj = self._get_version(plan_code, version)
        obj = selectors.get_placeholder_leave_by_code(leave_code)
        if obj is None or obj.version_id != version_obj.id:
            raise NotFoundException(
                resource="PlaceholderLeave",
                lookup_field="code",
                lookup_value=leave_code,
            )
        return obj

    def list_for_version(
        self, *, plan_code: str, version: int, params: ListParams | None = None
    ) -> PaginatedResult[PlaceholderLeave]:
        params = params or ListParams()
        version_obj = self._get_version(plan_code, version)
        qs = selectors.get_placeholder_leaves_for_version(version_obj)

        team_code = params.filters.get("team")
        if team_code:
            team = team_selectors.get_team_by_code(team_code)
            if team is None:
                raise NotFoundException(
                    resource="Team", lookup_field="code", lookup_value=team_code
                )
            member_ids = list(
                team_selectors.get_active_members_for_team(team).values_list(
                    "id", flat=True
                )
            )
            qs = qs.filter(member_id__in=member_ids)

        source = params.filters.get("source")
        if source in ("auto", "manual"):
            qs = qs.filter(is_auto=(source == "auto"))

        member_code = params.filters.get("member")
        if member_code:
            profile = user_selectors.get_member_by_code(member_code)
            if profile is None:
                raise NotFoundException(
                    resource="Member", lookup_field="code", lookup_value=member_code
                )
            qs = qs.filter(member_id=profile.user_id)

        sprint_code = params.filters.get("sprint")
        if sprint_code:
            sprint = sprint_selectors.get_sprint_by_code(sprint_code)
            if sprint is None:
                raise NotFoundException(
                    resource="Sprint", lookup_field="code", lookup_value=sprint_code
                )
            qs = qs.filter(sprint_id=sprint.id)

        if params.search:
            qs = qs.filter(
                Q(member__email__icontains=params.search)
                | Q(member__profile__display_name__icontains=params.search)
                | Q(notes__icontains=params.search)
            )

        return paginate_queryset(qs, params.page, params.page_size)

    @transaction.atomic
    def update(
        self,
        *,
        plan_code: str,
        version: int,
        leave_code: str,
        days: Decimal,
        notes: str,
    ) -> PlaceholderLeave:
        obj = self._get_placeholder_leave(
            plan_code=plan_code, version=version, leave_code=leave_code
        )
        before = self._snapshot(obj)

        obj.days = days
        obj.notes = notes
        # A manual edit takes this row out of the auto-generated pool — the
        # next regenerate() run must not silently overwrite it.
        obj.is_auto = False
        obj.updated_by = self.user
        obj.save(update_fields=["days", "notes", "is_auto", "updated_by", "updated_at"])

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                obj.version.plan, obj.version.version, obj
            ),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, *, plan_code: str, version: int, leave_code: str) -> None:
        obj = self._get_placeholder_leave(
            plan_code=plan_code, version=version, leave_code=leave_code
        )
        before = self._snapshot(obj)
        resource_code = self._resource_code(obj.version.plan, obj.version.version, obj)
        obj.delete()

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=resource_code,
            before=before,
            actor=self.user,
        )

    def regenerate(
        self,
        *,
        plan_code: str,
        version: int,
        include_current_sprint: bool = False,
        remove_overrides: bool = False,
    ) -> int:
        version_obj = self._get_version(plan_code, version)
        if remove_overrides:
            self.clear_overrides_for_version(version_obj)
        created = self.generate_for_version(
            version_obj, include_current_sprint, remove_overrides
        )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=f"{version_obj.plan.code}-v{version_obj.version}",
            before={},
            after={"regenerated_count": created},
            actor=self.user,
        )
        return created

    @staticmethod
    def _round_half(value: Decimal) -> Decimal:
        return (value * 2).quantize(Decimal("1"), rounding=ROUND_HALF_UP) / 2

    @staticmethod
    def _distribute_days(
        total_days: Decimal, sprint_caps: list[tuple[Sprint, Decimal]]
    ) -> dict[int, Decimal]:
        if total_days <= 0 or not sprint_caps:
            return {}

        order = [sprint for sprint, _ in sprint_caps]
        caps_remaining = {sprint.id: cap for sprint, cap in sprint_caps}
        allocation: dict[int, Decimal] = {}
        remaining = total_days

        base_share = PlaceholderLeaveService._round_half(total_days / len(order))
        for sprint in order:
            give = PlaceholderLeaveService._round_half(
                min(base_share, caps_remaining[sprint.id], remaining)
            )
            if give > 0:
                allocation[sprint.id] = give
                caps_remaining[sprint.id] -= give
                remaining -= give

        while remaining > 0:
            progressed = False
            for sprint in order:
                if remaining <= 0:
                    break
                room = caps_remaining[sprint.id]
                if room <= 0:
                    continue
                give = min(Decimal("0.5"), room, remaining)
                if give <= 0:
                    continue
                allocation[sprint.id] = allocation.get(sprint.id, Decimal("0")) + give
                caps_remaining[sprint.id] -= give
                remaining -= give
                progressed = True
            if not progressed:
                break

        return allocation

    def clear_overrides_for_version(self, version: PlanVersion) -> int:
        with transaction.atomic():
            deleted_count, _ = PlaceholderLeave.objects.filter(version=version).delete()
            if version.has_leave_overrides:
                version.has_leave_overrides = False
                version.save(update_fields=["has_leave_overrides"])
        return deleted_count

    def generate_for_version(
        self,
        version: PlanVersion,
        include_current_sprint: bool,
        remove_overrides: bool,
    ) -> int:
        fy = version.plan.financial_year
        sprints = list(sprint_selectors.get_sprints_for_fy(fy.code))
        half_index = len(sprints) // 2
        second_half = sprints[half_index:]
        eligible_sprints = [
            s
            for s in second_half
            if s.status == SprintStatus.FUTURE
            or (include_current_sprint and s.status == SprintStatus.IN_PROGRESS)
        ]

        teams = selectors.get_teams_for_version(version)
        members: dict[int, User] = {}
        for team in teams:
            for member in team_selectors.get_active_members_for_team(team):
                members[member.id] = member

        # (member_id, sprint_id) slots already occupied by a manual override —
        # never overwritten by auto-generation, regardless of remove_overrides.
        manual_slots = set(
            PlaceholderLeave.objects.filter(version=version, is_auto=False).values_list(
                "member_id", "sprint_id"
            )
        )

        allocations_by_member: dict[int, dict[int, Decimal]] = {}
        for member in members.values():
            profile = getattr(member, "profile", None)
            holidays = getattr(profile, "default_holidays", None) or 0
            used = leave_selectors.get_confirmed_leave_days_for_member_in_range(
                member, fy.start_date, fy.end_date
            )
            remaining = self._round_half(max(Decimal(holidays) - used, Decimal("0")))
            if remaining <= 0:
                continue

            sprint_caps = []
            for sprint in eligible_sprints:
                capacity = sprint_selectors.get_capacity_for_member_sprint(
                    member, sprint
                )
                cap = capacity.net_capacity if capacity else Decimal("0")
                if cap > 0:
                    sprint_caps.append((sprint, cap))

            allocation = self._distribute_days(remaining, sprint_caps)
            if allocation:
                allocations_by_member[member.id] = allocation

        # PlaceholderLeave extends CodeModel, whose `code` field is only
        # populated inside an overridden save() — bulk_create() bypasses
        # save() entirely, leaving `code` blank on every row and colliding
        # on its unique constraint. Individual create() calls are required
        # so each row's code is generated correctly.
        created_count = 0
        with transaction.atomic():
            PlaceholderLeave.objects.filter(version=version, is_auto=True).delete()
            for member_id, allocation in allocations_by_member.items():
                member = members[member_id]
                for sprint_id, days in allocation.items():
                    if (member_id, sprint_id) in manual_slots:
                        continue
                    PlaceholderLeave.objects.create(
                        version=version,
                        member=member,
                        sprint_id=sprint_id,
                        days=days,
                        is_auto=True,
                    )
                    created_count += 1
        return created_count
