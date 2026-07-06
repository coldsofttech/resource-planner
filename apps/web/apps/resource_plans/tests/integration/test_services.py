import datetime
from decimal import Decimal

from django.test import TestCase

from apps.core.exceptions import ValidationException
from apps.financial_years.tests.factories import make_financial_year
from apps.leaves.models import Leave, LeaveDayEntry
from apps.projects.tests.factories import make_project
from apps.resource_plans.constants import (
    Confidence,
    DependencyType,
    Priority,
    SplitMode,
)
from apps.resource_plans.models import (
    Allocation,
    MemberCapacity,
    PlaceholderEngineer,
    PlaceholderLeave,
    PlanPhasePause,
)
from apps.resource_plans.services.allocation_engine import AllocationEngineService
from apps.resource_plans.services.capacity_snapshot import CapacitySnapshotService
from apps.resource_plans.services.dependency_graph import DependencyGraphService
from apps.resource_plans.services.placeholder_leave import PlaceholderLeaveService
from apps.resource_plans.tests.factories import (
    make_engine_job,
    make_plan,
    make_plan_assignment,
    make_plan_phase,
    make_plan_phase_dependency,
    make_plan_version,
    make_plan_version_project,
    make_plan_version_team,
)
from apps.sprints.constants import SprintStatus
from apps.sprints.models import Capacity
from apps.sprints.tests.factories import make_capacity, make_sprint
from apps.teams.models import Assignment
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_profile, make_user


class ClearOverridesForVersionTest(TestCase):
    def test_deletes_all_rows_and_resets_flag(self):
        version = make_plan_version()
        version.has_leave_overrides = True
        version.save(update_fields=["has_leave_overrides"])
        sprint = make_sprint()
        member_a = make_user(email="member-a@example.com")
        member_b = make_user(email="member-b@example.com")
        PlaceholderLeave.objects.create(
            version=version,
            member=member_a,
            sprint=sprint,
            days=Decimal("1"),
            is_auto=True,
        )
        PlaceholderLeave.objects.create(
            version=version,
            member=member_b,
            sprint=sprint,
            days=Decimal("1"),
            is_auto=False,
        )

        deleted = PlaceholderLeaveService().clear_overrides_for_version(version)

        self.assertEqual(deleted, 2)
        self.assertEqual(PlaceholderLeave.objects.filter(version=version).count(), 0)
        version.refresh_from_db()
        self.assertFalse(version.has_leave_overrides)

    def test_no_rows_returns_zero_and_flag_stays_false(self):
        version = make_plan_version()

        deleted = PlaceholderLeaveService().clear_overrides_for_version(version)

        self.assertEqual(deleted, 0)
        version.refresh_from_db()
        self.assertFalse(version.has_leave_overrides)


class GenerateForVersionTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=datetime.date(2024, 4, 1), end_date=datetime.date(2025, 3, 31)
        )
        self.plan = make_plan(financial_year=self.fy)
        self.version = make_plan_version(plan=self.plan)
        self.plan_project = make_plan_version_project(version=self.version)
        self.team = make_team(name="Engine Team")
        self.plan_version_team = make_plan_version_team(
            plan_project=self.plan_project, team=self.team
        )

        # 4 sprints in the FY: 1-2 in the first half, 3-4 in the second half.
        self.sprint1 = make_sprint(
            financial_year=self.fy, sprint_number=1, status=SprintStatus.EXPIRED
        )
        self.sprint2 = make_sprint(
            financial_year=self.fy, sprint_number=2, status=SprintStatus.EXPIRED
        )
        self.sprint3 = make_sprint(
            financial_year=self.fy, sprint_number=3, status=SprintStatus.FUTURE
        )
        self.sprint4 = make_sprint(
            financial_year=self.fy, sprint_number=4, status=SprintStatus.FUTURE
        )

        self.member = make_user(email="engineer@example.com")
        make_profile(user=self.member, default_holidays=10)
        # Assigning the member to a team triggers `_on_assignment_change`,
        # which auto-generates Capacity rows for every active/future sprint
        # via SprintCapacityEngine — so the rows already exist by this
        # point; overwrite their net_capacity to fixed test values instead
        # of creating new rows (which would violate the unique constraint).
        Assignment.objects.create(team=self.team, member=self.member)
        Capacity.objects.filter(sprint=self.sprint3, member=self.member).update(
            net_capacity=Decimal("5")
        )
        Capacity.objects.filter(sprint=self.sprint4, member=self.member).update(
            net_capacity=Decimal("5")
        )

    def test_distributes_full_entitlement_across_second_half_future_sprints(self):
        created = PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )

        self.assertEqual(created, 2)
        rows = PlaceholderLeave.objects.filter(version=self.version, member=self.member)
        self.assertEqual(rows.count(), 2)
        self.assertEqual(sum(r.days for r in rows), Decimal("10"))
        for row in rows:
            self.assertTrue(row.is_auto)
            self.assertIn(row.sprint_id, [self.sprint3.id, self.sprint4.id])

    def test_first_half_sprints_never_receive_placeholder_leave(self):
        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )

        self.assertFalse(
            PlaceholderLeave.objects.filter(
                version=self.version, sprint__in=[self.sprint1, self.sprint2]
            ).exists()
        )

    def test_expired_second_half_sprint_excluded(self):
        self.sprint3.status = SprintStatus.EXPIRED
        self.sprint3.save(update_fields=["status"])

        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )

        self.assertFalse(
            PlaceholderLeave.objects.filter(
                version=self.version, sprint=self.sprint3
            ).exists()
        )
        self.assertTrue(
            PlaceholderLeave.objects.filter(
                version=self.version, sprint=self.sprint4
            ).exists()
        )

    def test_in_progress_sprint_included_only_when_flag_set(self):
        self.sprint4.status = SprintStatus.IN_PROGRESS
        self.sprint4.save(update_fields=["status"])

        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )
        self.assertFalse(
            PlaceholderLeave.objects.filter(
                version=self.version, sprint=self.sprint4
            ).exists()
        )

        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=True, remove_overrides=False
        )
        self.assertTrue(
            PlaceholderLeave.objects.filter(
                version=self.version, sprint=self.sprint4
            ).exists()
        )

    def test_entitlement_nets_confirmed_leave_days_in_fy(self):
        leave = Leave.objects.create(
            member=self.member,
            start_date=datetime.date(2024, 5, 1),
            end_date=datetime.date(2024, 5, 4),
            days=Decimal("4"),
        )
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2024, 5, 1))
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2024, 5, 2))
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2024, 5, 3))
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2024, 5, 4))

        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )

        rows = PlaceholderLeave.objects.filter(version=self.version, member=self.member)
        self.assertEqual(sum(r.days for r in rows), Decimal("6"))

    def test_member_with_no_default_holidays_produces_no_rows(self):
        self.member.profile.default_holidays = None
        self.member.profile.save(update_fields=["default_holidays"])

        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )

        self.assertFalse(
            PlaceholderLeave.objects.filter(
                version=self.version, member=self.member
            ).exists()
        )

    def test_allocation_respects_capacity_cap_per_sprint(self):
        Capacity.objects.filter(sprint=self.sprint3, member=self.member).update(
            net_capacity=Decimal("2")
        )

        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )

        sprint3_row = PlaceholderLeave.objects.filter(
            version=self.version, member=self.member, sprint=self.sprint3
        ).first()
        if sprint3_row:
            self.assertLessEqual(sprint3_row.days, Decimal("2"))

    def test_rerun_regenerates_auto_rows_without_duplicating(self):
        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )
        first_count = PlaceholderLeave.objects.filter(
            version=self.version, is_auto=True
        ).count()

        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )
        second_count = PlaceholderLeave.objects.filter(
            version=self.version, is_auto=True
        ).count()

        self.assertEqual(first_count, second_count)

    def test_manual_override_preserved_and_auto_skips_that_slot(self):
        manual = PlaceholderLeave.objects.create(
            version=self.version,
            member=self.member,
            sprint=self.sprint3,
            days=Decimal("3"),
            is_auto=False,
        )

        PlaceholderLeaveService().generate_for_version(
            self.version, include_current_sprint=False, remove_overrides=False
        )

        manual.refresh_from_db()
        self.assertFalse(manual.is_auto)
        self.assertEqual(manual.days, Decimal("3"))
        # The auto-generation attempt for (version, member, sprint3) is silently
        # skipped via ignore_conflicts=True since the manual row already
        # occupies that slot.
        self.assertEqual(
            PlaceholderLeave.objects.filter(
                version=self.version, member=self.member, sprint=self.sprint3
            ).count(),
            1,
        )


class SyncForVersionTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=datetime.date(2024, 4, 1), end_date=datetime.date(2025, 3, 31)
        )
        self.plan = make_plan(financial_year=self.fy)
        self.version = make_plan_version(plan=self.plan)
        self.plan_project = make_plan_version_project(version=self.version)
        self.team = make_team(name="Capacity Team")
        make_plan_version_team(plan_project=self.plan_project, team=self.team)

        self.sprint_past = make_sprint(
            financial_year=self.fy, sprint_number=1, status=SprintStatus.EXPIRED
        )
        self.sprint_future = make_sprint(
            financial_year=self.fy, sprint_number=2, status=SprintStatus.FUTURE
        )

        self.member = make_user(email="capacity-engineer@example.com")
        make_profile(user=self.member)
        # Assigning triggers `_on_assignment_change`, which auto-generates a
        # Capacity row for the FUTURE sprint only (EXPIRED sprints are
        # excluded from `get_active_and_future_sprints`) — create the past
        # sprint's Capacity manually and overwrite the future one's values.
        Assignment.objects.create(team=self.team, member=self.member)
        make_capacity(
            sprint=self.sprint_past,
            member=self.member,
            working_days=Decimal("10"),
            holiday_days=Decimal("1"),
            leave_days=Decimal("0"),
            net_capacity=Decimal("9"),
        )
        Capacity.objects.filter(sprint=self.sprint_future, member=self.member).update(
            working_days=Decimal("10"),
            holiday_days=Decimal("0"),
            leave_days=Decimal("2"),
            net_capacity=Decimal("8"),
        )

    def test_snapshot_includes_all_fy_sprints_not_just_future(self):
        created = CapacitySnapshotService().sync_for_version(self.version)

        self.assertEqual(created, 2)
        self.assertTrue(
            MemberCapacity.objects.filter(
                version=self.version, member=self.member, sprint=self.sprint_past
            ).exists()
        )
        self.assertTrue(
            MemberCapacity.objects.filter(
                version=self.version, member=self.member, sprint=self.sprint_future
            ).exists()
        )

    def test_snapshot_fields_mirror_capacity(self):
        CapacitySnapshotService().sync_for_version(self.version)

        row = MemberCapacity.objects.get(
            version=self.version, member=self.member, sprint=self.sprint_future
        )
        self.assertEqual(row.working_days, Decimal("10"))
        self.assertEqual(row.holiday_days, Decimal("0"))
        self.assertEqual(row.leave_days, Decimal("2"))
        self.assertEqual(row.placeholder_leave_days, Decimal("0"))
        self.assertEqual(row.net_capacity, Decimal("8"))
        self.assertIsNotNone(row.synced_at)

    def test_snapshot_subtracts_placeholder_leave_from_net_capacity(self):
        PlaceholderLeave.objects.create(
            version=self.version,
            member=self.member,
            sprint=self.sprint_future,
            days=Decimal("3"),
            is_auto=True,
        )

        CapacitySnapshotService().sync_for_version(self.version)

        row = MemberCapacity.objects.get(
            version=self.version, member=self.member, sprint=self.sprint_future
        )
        self.assertEqual(row.placeholder_leave_days, Decimal("3"))
        self.assertEqual(row.net_capacity, Decimal("5"))

    def test_snapshot_floors_negative_net_capacity_at_zero(self):
        PlaceholderLeave.objects.create(
            version=self.version,
            member=self.member,
            sprint=self.sprint_future,
            days=Decimal("20"),
            is_auto=True,
        )

        CapacitySnapshotService().sync_for_version(self.version)

        row = MemberCapacity.objects.get(
            version=self.version, member=self.member, sprint=self.sprint_future
        )
        self.assertEqual(row.net_capacity, Decimal("0"))

    def test_full_resync_replaces_stale_rows_not_duplicates(self):
        CapacitySnapshotService().sync_for_version(self.version)
        first_count = MemberCapacity.objects.filter(version=self.version).count()

        Capacity.objects.filter(sprint=self.sprint_future, member=self.member).update(
            net_capacity=Decimal("4")
        )
        CapacitySnapshotService().sync_for_version(self.version)
        second_count = MemberCapacity.objects.filter(version=self.version).count()

        self.assertEqual(first_count, second_count)
        row = MemberCapacity.objects.get(
            version=self.version, member=self.member, sprint=self.sprint_future
        )
        self.assertEqual(row.net_capacity, Decimal("4"))

    def test_member_not_assigned_to_version_teams_excluded(self):
        outsider = make_user(email="outsider@example.com")
        make_capacity(
            sprint=self.sprint_future, member=outsider, net_capacity=Decimal("5")
        )

        CapacitySnapshotService().sync_for_version(self.version)

        self.assertFalse(
            MemberCapacity.objects.filter(
                version=self.version, member=outsider
            ).exists()
        )

    def test_no_assigned_members_creates_nothing(self):
        Assignment.objects.filter(team=self.team, member=self.member).delete()

        created = CapacitySnapshotService().sync_for_version(self.version)

        self.assertEqual(created, 0)
        self.assertEqual(MemberCapacity.objects.filter(version=self.version).count(), 0)


class SyncRecordTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=datetime.date(2024, 4, 1), end_date=datetime.date(2025, 3, 31)
        )
        self.plan = make_plan(financial_year=self.fy)
        self.version = make_plan_version(plan=self.plan)
        self.sprint = make_sprint(
            financial_year=self.fy, sprint_number=1, status=SprintStatus.FUTURE
        )
        self.member = make_user(email="sync-record-engineer@example.com")
        self.capacity = make_capacity(
            sprint=self.sprint,
            member=self.member,
            working_days=Decimal("10"),
            holiday_days=Decimal("0"),
            leave_days=Decimal("1"),
            net_capacity=Decimal("9"),
        )

    def test_creates_new_snapshot_row(self):
        obj = CapacitySnapshotService().sync_record(
            self.version, self.member.id, self.sprint.id
        )

        self.assertIsNotNone(obj)
        self.assertEqual(obj.net_capacity, Decimal("9"))
        self.assertEqual(obj.placeholder_leave_days, Decimal("0"))

    def test_updates_existing_snapshot_row(self):
        CapacitySnapshotService().sync_record(
            self.version, self.member.id, self.sprint.id
        )
        self.capacity.net_capacity = Decimal("7")
        self.capacity.save(update_fields=["net_capacity"])

        obj = CapacitySnapshotService().sync_record(
            self.version, self.member.id, self.sprint.id
        )

        self.assertEqual(
            MemberCapacity.objects.filter(
                version=self.version, member=self.member, sprint=self.sprint
            ).count(),
            1,
        )
        self.assertEqual(obj.net_capacity, Decimal("7"))

    def test_nets_placeholder_leave_and_floors_at_zero(self):
        PlaceholderLeave.objects.create(
            version=self.version,
            member=self.member,
            sprint=self.sprint,
            days=Decimal("15"),
            is_auto=True,
        )

        obj = CapacitySnapshotService().sync_record(
            self.version, self.member.id, self.sprint.id
        )

        self.assertEqual(obj.placeholder_leave_days, Decimal("15"))
        self.assertEqual(obj.net_capacity, Decimal("0"))

    def test_no_underlying_capacity_deletes_stale_snapshot_row(self):
        CapacitySnapshotService().sync_record(
            self.version, self.member.id, self.sprint.id
        )
        self.capacity.delete()

        obj = CapacitySnapshotService().sync_record(
            self.version, self.member.id, self.sprint.id
        )

        self.assertIsNone(obj)
        self.assertFalse(
            MemberCapacity.objects.filter(
                version=self.version, member=self.member, sprint=self.sprint
            ).exists()
        )


class TopologicalSortTest(TestCase):
    def setUp(self):
        self.version = make_plan_version()
        self.plan_project = make_plan_version_project(version=self.version)
        self.team = make_team(name="Graph Team")
        self.plan_version_team = make_plan_version_team(
            plan_project=self.plan_project, team=self.team
        )

    def _phase(self, name, sequence_order=1, end_sprint=None):
        return make_plan_phase(
            plan_project_team=self.plan_version_team,
            name=name,
            sequence_order=sequence_order,
            end_sprint=end_sprint,
        )

    def test_orders_by_dependency_edge(self):
        phase_a = self._phase("A")
        phase_b = self._phase("B")
        make_plan_phase_dependency(phase=phase_b, predecessor_phase=phase_a)

        proj_by_phase_id = {
            phase_a.id: self.plan_project,
            phase_b.id: self.plan_project,
        }
        result = DependencyGraphService.topological_sort(
            [phase_a, phase_b], proj_by_phase_id
        )

        self.assertEqual([p.id for p in result], [phase_a.id, phase_b.id])

    def test_tie_break_by_priority_when_no_dependency_between_phases(self):
        low_project = make_plan_version_project(
            version=self.version,
            project=make_project(name="Priority Low Project"),
            priority_snapshot=str(Priority.LOW),
        )
        low_team = make_plan_version_team(plan_project=low_project, team=self.team)
        high_project = make_plan_version_project(
            version=self.version,
            project=make_project(name="Priority High Project"),
            priority_snapshot=str(Priority.HIGH),
        )
        high_team = make_plan_version_team(plan_project=high_project, team=self.team)

        phase_low = make_plan_phase(plan_project_team=low_team, name="Low")
        phase_high = make_plan_phase(plan_project_team=high_team, name="High")

        proj_by_phase_id = {phase_low.id: low_project, phase_high.id: high_project}
        result = DependencyGraphService.topological_sort(
            [phase_low, phase_high], proj_by_phase_id
        )

        self.assertEqual([p.id for p in result], [phase_high.id, phase_low.id])

    def test_tie_break_by_dates_strict_before_priority(self):
        strict_project = make_plan_version_project(
            version=self.version,
            project=make_project(name="Strict Project"),
            dates_strict=True,
            priority_snapshot=str(Priority.LOW),
        )
        strict_team = make_plan_version_team(
            plan_project=strict_project, team=self.team
        )
        loose_project = make_plan_version_project(
            version=self.version,
            project=make_project(name="Loose Project"),
            dates_strict=False,
            priority_snapshot=str(Priority.HIGH),
        )
        loose_team = make_plan_version_team(plan_project=loose_project, team=self.team)

        phase_strict = make_plan_phase(plan_project_team=strict_team, name="Strict")
        phase_loose = make_plan_phase(plan_project_team=loose_team, name="Loose")

        proj_by_phase_id = {
            phase_strict.id: strict_project,
            phase_loose.id: loose_project,
        }
        result = DependencyGraphService.topological_sort(
            [phase_strict, phase_loose], proj_by_phase_id
        )

        self.assertEqual([p.id for p in result], [phase_strict.id, phase_loose.id])

    def test_tie_break_by_confidence_when_priority_ties(self):
        low_confidence_project = make_plan_version_project(
            version=self.version,
            project=make_project(name="Low Confidence Project"),
            confidence_snapshot=str(Confidence.LOW),
        )
        low_team = make_plan_version_team(
            plan_project=low_confidence_project, team=self.team
        )
        high_confidence_project = make_plan_version_project(
            version=self.version,
            project=make_project(name="High Confidence Project"),
            confidence_snapshot=str(Confidence.HIGH),
        )
        high_team = make_plan_version_team(
            plan_project=high_confidence_project, team=self.team
        )

        phase_low = make_plan_phase(plan_project_team=low_team, name="LowConf")
        phase_high = make_plan_phase(plan_project_team=high_team, name="HighConf")

        proj_by_phase_id = {
            phase_low.id: low_confidence_project,
            phase_high.id: high_confidence_project,
        }
        result = DependencyGraphService.topological_sort(
            [phase_low, phase_high], proj_by_phase_id
        )

        self.assertEqual([p.id for p in result], [phase_high.id, phase_low.id])

    def test_tie_break_by_end_sprint_when_priority_and_confidence_tie(self):
        sprint_early = make_sprint(sprint_number=1)
        sprint_late = make_sprint(
            financial_year=sprint_early.financial_year, sprint_number=2
        )
        phase_late = self._phase("Late", end_sprint=sprint_late)
        phase_early = self._phase("Early", end_sprint=sprint_early)

        proj_by_phase_id = {
            phase_late.id: self.plan_project,
            phase_early.id: self.plan_project,
        }
        result = DependencyGraphService.topological_sort(
            [phase_late, phase_early], proj_by_phase_id
        )

        self.assertEqual([p.id for p in result], [phase_early.id, phase_late.id])

    def test_tie_break_by_sequence_order_as_final_fallback(self):
        phase_second = self._phase("Second", sequence_order=2)
        phase_first = self._phase("First", sequence_order=1)

        proj_by_phase_id = {
            phase_second.id: self.plan_project,
            phase_first.id: self.plan_project,
        }
        result = DependencyGraphService.topological_sort(
            [phase_second, phase_first], proj_by_phase_id
        )

        self.assertEqual([p.id for p in result], [phase_first.id, phase_second.id])

    def test_defensively_ignores_predecessor_outside_given_scope(self):
        outside_phase = self._phase("Outside")
        phase_b = self._phase("B")
        make_plan_phase_dependency(phase=phase_b, predecessor_phase=outside_phase)

        # outside_phase is deliberately NOT included in the `phases` list —
        # its dependency edge must not permanently block phase_b.
        proj_by_phase_id = {phase_b.id: self.plan_project}
        result = DependencyGraphService.topological_sort([phase_b], proj_by_phase_id)

        self.assertEqual([p.id for p in result], [phase_b.id])

    def test_raises_on_circular_dependency(self):
        phase_a = self._phase("A")
        phase_b = self._phase("B")
        make_plan_phase_dependency(phase=phase_a, predecessor_phase=phase_b)
        make_plan_phase_dependency(phase=phase_b, predecessor_phase=phase_a)

        proj_by_phase_id = {
            phase_a.id: self.plan_project,
            phase_b.id: self.plan_project,
        }
        with self.assertRaises(ValidationException):
            DependencyGraphService.topological_sort(
                [phase_a, phase_b], proj_by_phase_id
            )


class EarliestStartTest(TestCase):
    def setUp(self):
        self.version = make_plan_version()
        self.plan_project = make_plan_version_project(version=self.version)
        self.team = make_team(name="Earliest Start Team")
        self.plan_version_team = make_plan_version_team(
            plan_project=self.plan_project, team=self.team
        )
        self.predecessor = make_plan_phase(
            plan_project_team=self.plan_version_team, name="Predecessor"
        )
        self.phase = make_plan_phase(
            plan_project_team=self.plan_version_team, name="Successor"
        )

    def test_no_dependencies_returns_none(self):
        result = DependencyGraphService.earliest_start(self.phase, {}, None)
        self.assertIsNone(result)

    def test_finish_to_start_adds_lag_after_predecessor_end(self):
        make_plan_phase_dependency(
            phase=self.phase,
            predecessor_phase=self.predecessor,
            dependency_type=str(DependencyType.FINISH_TO_START),
            lag_sprints=0,
        )
        completed = {self.predecessor.id: (1, 5)}

        result = DependencyGraphService.earliest_start(self.phase, completed, None)

        self.assertEqual(result, 6)

    def test_finish_to_start_with_positive_lag(self):
        make_plan_phase_dependency(
            phase=self.phase,
            predecessor_phase=self.predecessor,
            dependency_type=str(DependencyType.FINISH_TO_START),
            lag_sprints=2,
        )
        completed = {self.predecessor.id: (1, 5)}

        result = DependencyGraphService.earliest_start(self.phase, completed, None)

        self.assertEqual(result, 8)

    def test_start_to_start_adds_lag_after_predecessor_start(self):
        make_plan_phase_dependency(
            phase=self.phase,
            predecessor_phase=self.predecessor,
            dependency_type=str(DependencyType.START_TO_START),
            lag_sprints=1,
        )
        completed = {self.predecessor.id: (3, 9)}

        result = DependencyGraphService.earliest_start(self.phase, completed, None)

        self.assertEqual(result, 4)

    def test_ignores_predecessor_not_yet_completed(self):
        make_plan_phase_dependency(
            phase=self.phase,
            predecessor_phase=self.predecessor,
            dependency_type=str(DependencyType.FINISH_TO_START),
        )

        result = DependencyGraphService.earliest_start(self.phase, {}, None)

        self.assertIsNone(result)

    def test_clamped_to_max_available_sprint_number(self):
        make_plan_phase_dependency(
            phase=self.phase,
            predecessor_phase=self.predecessor,
            dependency_type=str(DependencyType.FINISH_TO_START),
        )
        completed = {self.predecessor.id: (1, 20)}

        result = DependencyGraphService.earliest_start(
            self.phase, completed, [1, 2, 3, 4, 5]
        )

        self.assertEqual(result, 5)

    def test_finds_nearest_valid_sprint_number_above_gap(self):
        make_plan_phase_dependency(
            phase=self.phase,
            predecessor_phase=self.predecessor,
            dependency_type=str(DependencyType.FINISH_TO_START),
        )
        completed = {self.predecessor.id: (1, 5)}

        result = DependencyGraphService.earliest_start(
            self.phase, completed, [1, 2, 3, 8, 9]
        )

        self.assertEqual(result, 8)


class AllocationEngineServiceTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=datetime.date(2024, 4, 1), end_date=datetime.date(2025, 3, 31)
        )
        self.plan = make_plan(financial_year=self.fy)
        self.version = make_plan_version(plan=self.plan)
        self.plan_project = make_plan_version_project(
            version=self.version, project=make_project(name="Alloc Project")
        )
        self.team = make_team(name="Alloc Team")
        self.plan_version_team = make_plan_version_team(
            plan_project=self.plan_project,
            team=self.team,
            allocated_days=Decimal("30"),
        )
        self.sprints = [
            make_sprint(
                financial_year=self.fy, sprint_number=n, status=SprintStatus.FUTURE
            )
            for n in range(1, 7)
        ]
        self.member = make_user(email="alloc-member@example.com")
        Assignment.objects.create(team=self.team, member=self.member)
        Capacity.objects.filter(member=self.member).update(net_capacity=Decimal("100"))
        CapacitySnapshotService().sync_for_version(self.version)
        self.job = make_engine_job(plan=self.plan, version=self.version)

    def _add_member(self, email):
        member = make_user(email=email)
        Assignment.objects.create(team=self.team, member=member)
        Capacity.objects.filter(member=member).update(net_capacity=Decimal("100"))
        CapacitySnapshotService().sync_for_version(self.version)
        return member

    def test_named_assignment_allocates_to_its_member(self):
        phase = make_plan_phase(
            plan_project_team=self.plan_version_team,
            days_effort=Decimal("9"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[2],
        )
        make_plan_assignment(phase=phase, member=self.member, auto_assign=False)

        allocation_set = AllocationEngineService().run(self.job)

        rows = Allocation.objects.filter(allocation_set=allocation_set, phase=phase)
        self.assertEqual(rows.count(), 3)
        self.assertEqual(sum(r.engine_days for r in rows), Decimal("9"))
        for row in rows:
            self.assertEqual(row.member_id, self.member.id)
            self.assertIsNone(row.placeholder_engineer_id)

    def test_explicit_zero_day_row_when_capacity_exhausted(self):
        phase = make_plan_phase(
            plan_project_team=self.plan_version_team,
            days_effort=Decimal("9"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[2],
        )
        make_plan_assignment(phase=phase, member=self.member, auto_assign=False)
        MemberCapacity.objects.filter(
            version=self.version, member=self.member, sprint=self.sprints[1]
        ).update(net_capacity=Decimal("0"))

        allocation_set = AllocationEngineService().run(self.job)

        row = Allocation.objects.get(
            allocation_set=allocation_set, phase=phase, sprint=self.sprints[1]
        )
        self.assertEqual(row.engine_days, Decimal("0"))

    def test_percent_split_mode_uses_split_value_as_percentage(self):
        phase = make_plan_phase(
            plan_project_team=self.plan_version_team,
            days_effort=Decimal("10"),
            split_mode=str(SplitMode.PERCENT),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[1],
        )
        member2 = self._add_member("alloc-member2@example.com")
        make_plan_assignment(phase=phase, member=self.member, split_value=Decimal("70"))
        make_plan_assignment(phase=phase, member=member2, split_value=Decimal("30"))

        allocation_set = AllocationEngineService().run(self.job)

        total_m1 = sum(
            r.engine_days
            for r in Allocation.objects.filter(
                allocation_set=allocation_set, member=self.member
            )
        )
        total_m2 = sum(
            r.engine_days
            for r in Allocation.objects.filter(
                allocation_set=allocation_set, member=member2
            )
        )
        self.assertEqual(total_m1, Decimal("7"))
        self.assertEqual(total_m2, Decimal("3"))

    def test_days_split_mode_uses_split_value_as_absolute_days(self):
        phase = make_plan_phase(
            plan_project_team=self.plan_version_team,
            days_effort=Decimal("10"),
            split_mode=str(SplitMode.DAYS),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[1],
        )
        make_plan_assignment(phase=phase, member=self.member, split_value=Decimal("4"))

        allocation_set = AllocationEngineService().run(self.job)

        total = sum(
            r.engine_days
            for r in Allocation.objects.filter(
                allocation_set=allocation_set, phase=phase
            )
        )
        self.assertEqual(total, Decimal("4"))

    def test_equal_split_mode_divides_evenly_across_assignments(self):
        phase = make_plan_phase(
            plan_project_team=self.plan_version_team,
            days_effort=Decimal("10"),
            split_mode=str(SplitMode.EQUAL),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[1],
        )
        member2 = self._add_member("alloc-member3@example.com")
        make_plan_assignment(phase=phase, member=self.member)
        make_plan_assignment(phase=phase, member=member2)

        allocation_set = AllocationEngineService().run(self.job)

        total_m1 = sum(
            r.engine_days
            for r in Allocation.objects.filter(
                allocation_set=allocation_set, member=self.member
            )
        )
        total_m2 = sum(
            r.engine_days
            for r in Allocation.objects.filter(
                allocation_set=allocation_set, member=member2
            )
        )
        self.assertEqual(total_m1, Decimal("5"))
        self.assertEqual(total_m2, Decimal("5"))

    def test_synthetic_assignment_created_when_phase_has_no_assignments(self):
        phase = make_plan_phase(
            plan_project_team=self.plan_version_team,
            days_effort=Decimal("6"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[1],
        )

        allocation_set = AllocationEngineService().run(self.job)

        rows = Allocation.objects.filter(allocation_set=allocation_set, phase=phase)
        self.assertEqual(rows.count(), 2)
        self.assertEqual(sum(r.engine_days for r in rows), Decimal("6"))
        self.assertTrue(all(r.member_id == self.member.id for r in rows))

    def test_auto_assign_picks_least_loaded_team_member(self):
        member2 = self._add_member("alloc-member4@example.com")

        phase1 = make_plan_phase(
            plan_project_team=self.plan_version_team,
            name="Phase1",
            days_effort=Decimal("20"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=1,
        )
        make_plan_assignment(phase=phase1, member=self.member, auto_assign=False)

        phase2 = make_plan_phase(
            plan_project_team=self.plan_version_team,
            name="Phase2",
            days_effort=Decimal("5"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=2,
        )
        make_plan_assignment(phase=phase2, member=self.member, auto_assign=True)

        allocation_set = AllocationEngineService().run(self.job)

        phase2_rows = Allocation.objects.filter(
            allocation_set=allocation_set, phase=phase2
        )
        self.assertTrue(all(r.member_id == member2.id for r in phase2_rows))

    def test_creates_placeholder_engineer_when_team_has_no_members(self):
        empty_team = make_team(name="Empty Team")
        empty_pvt = make_plan_version_team(
            plan_project=self.plan_project,
            team=empty_team,
            allocated_days=Decimal("10"),
        )
        phase = make_plan_phase(
            plan_project_team=empty_pvt,
            days_effort=Decimal("5"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
        )

        allocation_set = AllocationEngineService().run(self.job)

        row = Allocation.objects.get(allocation_set=allocation_set, phase=phase)
        self.assertIsNone(row.member_id)
        self.assertIsNotNone(row.placeholder_engineer_id)
        placeholder = PlaceholderEngineer.objects.get(id=row.placeholder_engineer_id)
        self.assertEqual(placeholder.team_id, empty_team.id)

    def test_reuses_placeholder_engineer_when_sprints_dont_overlap(self):
        empty_team = make_team(name="Empty Team 2")
        empty_pvt = make_plan_version_team(
            plan_project=self.plan_project,
            team=empty_team,
            allocated_days=Decimal("10"),
        )
        phase1 = make_plan_phase(
            plan_project_team=empty_pvt,
            name="P1",
            days_effort=Decimal("2"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=1,
        )
        phase2 = make_plan_phase(
            plan_project_team=empty_pvt,
            name="P2",
            days_effort=Decimal("2"),
            start_sprint=self.sprints[3],
            end_sprint=self.sprints[3],
            sequence_order=2,
        )

        allocation_set = AllocationEngineService().run(self.job)

        row1 = Allocation.objects.get(allocation_set=allocation_set, phase=phase1)
        row2 = Allocation.objects.get(allocation_set=allocation_set, phase=phase2)
        self.assertEqual(row1.placeholder_engineer_id, row2.placeholder_engineer_id)
        self.assertEqual(PlaceholderEngineer.objects.filter(team=empty_team).count(), 1)

    def test_creates_new_placeholder_slot_when_existing_slot_is_busy(self):
        empty_team = make_team(name="Empty Team 3")
        empty_pvt = make_plan_version_team(
            plan_project=self.plan_project,
            team=empty_team,
            allocated_days=Decimal("10"),
        )
        phase1 = make_plan_phase(
            plan_project_team=empty_pvt,
            name="P1",
            days_effort=Decimal("2"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=1,
        )
        phase2 = make_plan_phase(
            plan_project_team=empty_pvt,
            name="P2",
            days_effort=Decimal("2"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=2,
        )

        allocation_set = AllocationEngineService().run(self.job)

        row1 = Allocation.objects.get(allocation_set=allocation_set, phase=phase1)
        row2 = Allocation.objects.get(allocation_set=allocation_set, phase=phase2)
        self.assertNotEqual(row1.placeholder_engineer_id, row2.placeholder_engineer_id)
        self.assertEqual(PlaceholderEngineer.objects.filter(team=empty_team).count(), 2)

    def test_capacity_cap_shared_across_phases_for_same_member(self):
        MemberCapacity.objects.filter(
            version=self.version, member=self.member, sprint=self.sprints[0]
        ).update(net_capacity=Decimal("5"))
        phase1 = make_plan_phase(
            plan_project_team=self.plan_version_team,
            name="P1",
            days_effort=Decimal("4"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=1,
        )
        make_plan_assignment(phase=phase1, member=self.member, auto_assign=False)
        phase2 = make_plan_phase(
            plan_project_team=self.plan_version_team,
            name="P2",
            days_effort=Decimal("4"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=2,
        )
        make_plan_assignment(phase=phase2, member=self.member, auto_assign=False)

        allocation_set = AllocationEngineService().run(self.job)

        row1 = Allocation.objects.get(
            allocation_set=allocation_set, phase=phase1, sprint=self.sprints[0]
        )
        row2 = Allocation.objects.get(
            allocation_set=allocation_set, phase=phase2, sprint=self.sprints[0]
        )
        self.assertEqual(row1.engine_days, Decimal("4"))
        self.assertEqual(row2.engine_days, Decimal("1"))

    def test_phase_pause_excludes_sprints_from_window(self):
        phase = make_plan_phase(
            plan_project_team=self.plan_version_team,
            days_effort=Decimal("4"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[3],
        )
        make_plan_assignment(phase=phase, member=self.member, auto_assign=False)
        PlanPhasePause.objects.create(
            phase=phase,
            pause_from=self.sprints[1],
            input_mode="sprint",
            resume_sprint=self.sprints[3],
        )

        allocation_set = AllocationEngineService().run(self.job)

        rows = Allocation.objects.filter(allocation_set=allocation_set, phase=phase)
        sprint_numbers = sorted(r.sprint.sprint_number for r in rows)
        self.assertEqual(sprint_numbers, [1, 4])

    def test_dependent_phase_starts_after_predecessor_ends(self):
        phase_a = make_plan_phase(
            plan_project_team=self.plan_version_team,
            name="A",
            days_effort=Decimal("2"),
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=1,
        )
        phase_b = make_plan_phase(
            plan_project_team=self.plan_version_team,
            name="B",
            days_effort=Decimal("2"),
            sequence_order=2,
        )
        make_plan_phase_dependency(phase=phase_b, predecessor_phase=phase_a)
        make_plan_assignment(phase=phase_a, member=self.member, auto_assign=False)
        make_plan_assignment(phase=phase_b, member=self.member, auto_assign=False)

        allocation_set = AllocationEngineService().run(self.job)

        rows_b = Allocation.objects.filter(allocation_set=allocation_set, phase=phase_b)
        min_sprint_number_b = min(r.sprint.sprint_number for r in rows_b)
        self.assertGreaterEqual(min_sprint_number_b, 2)

    def test_days_effort_falls_back_to_team_allocated_days_split_across_phases(self):
        fallback_team = make_team(name="Fallback Team")
        fallback_pvt = make_plan_version_team(
            plan_project=self.plan_project,
            team=fallback_team,
            allocated_days=Decimal("20"),
        )
        fallback_member = make_user(email="fallback-member@example.com")
        Assignment.objects.create(team=fallback_team, member=fallback_member)
        Capacity.objects.filter(member=fallback_member).update(
            net_capacity=Decimal("100")
        )
        CapacitySnapshotService().sync_for_version(self.version)

        phase1 = make_plan_phase(
            plan_project_team=fallback_pvt,
            name="F1",
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=1,
        )
        phase2 = make_plan_phase(
            plan_project_team=fallback_pvt,
            name="F2",
            start_sprint=self.sprints[0],
            end_sprint=self.sprints[0],
            sequence_order=2,
        )
        make_plan_assignment(phase=phase1, member=fallback_member, auto_assign=False)
        make_plan_assignment(phase=phase2, member=fallback_member, auto_assign=False)

        allocation_set = AllocationEngineService().run(self.job)

        total1 = sum(
            r.engine_days
            for r in Allocation.objects.filter(
                allocation_set=allocation_set, phase=phase1
            )
        )
        total2 = sum(
            r.engine_days
            for r in Allocation.objects.filter(
                allocation_set=allocation_set, phase=phase2
            )
        )
        self.assertEqual(total1, Decimal("10"))
        self.assertEqual(total2, Decimal("10"))
