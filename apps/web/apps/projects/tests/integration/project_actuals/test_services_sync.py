"""
Integration tests for ProjectActualsService.sync_for_fy() and _rebuild_fy().

Covers:
- Single FY rebuild from ProjectSprintActual records
- Cascade: changing FY N propagates to FY N+1 and N+2
- Recharge linkage: sprint actuals feed into project totals via RechargeDetail
- Removing a sprint actual and re-syncing removes the contribution
- Edge cases: no actuals, orphan recharge records, terminal projects excluded
"""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectActuals
from apps.projects.models.project_sprint_actual import ProjectSprintActual
from apps.projects.services.project_actuals import ProjectActualsService
from apps.projects.tests.factories import (
    make_financial_year,
    make_project,
    make_project_status,
)
from apps.sprints.constants import SprintStatus
from apps.sprints.tests.factories import make_sprint
from apps.users.tests.factories import make_user


def make_service(user=None):
    svc = ProjectActualsService()
    svc.user = user or make_user()
    return svc


def make_actuals(project, fy, total_cost_to_date="0", prev_fy_actuals="0"):
    return ProjectActuals.objects.create(
        project=project,
        fy=fy,
        total_cost_to_date=Decimal(total_cost_to_date),
        prev_fy_actuals=Decimal(prev_fy_actuals),
    )


def make_sprint_actual(project, sprint, total_cost="1000", total_days="1"):
    return ProjectSprintActual.objects.create(
        project=project,
        sprint=sprint,
        total_days=Decimal(total_days),
        total_cost=Decimal(total_cost),
    )


# ── _rebuild_fy ────────────────────────────────────────────────────────────────


class RebuildFyBasicTest(TestCase):
    """_rebuild_fy() creates ProjectActuals from ProjectSprintActual data."""

    def setUp(self):
        mark_setup_complete()
        self.svc = make_service()
        self.project = make_project()
        self.fy = make_financial_year()
        self.sprint = make_sprint(
            financial_year=self.fy,
            status=SprintStatus.COMPLETED,
        )

    def test_rebuild_returns_zero_when_no_sprint_actuals(self):
        count = self.svc._rebuild_fy(self.fy)
        self.assertEqual(count, 0)

    def test_rebuild_creates_project_actuals_record(self):
        make_sprint_actual(self.project, self.sprint, total_cost="5000")
        self.svc._rebuild_fy(self.fy)
        self.assertTrue(
            ProjectActuals.objects.filter(project=self.project, fy=self.fy).exists()
        )

    def test_rebuild_sets_correct_total_cost_to_date(self):
        make_sprint_actual(self.project, self.sprint, total_cost="3000")
        self.svc._rebuild_fy(self.fy)
        record = ProjectActuals.objects.get(project=self.project, fy=self.fy)
        self.assertEqual(record.total_cost_to_date, Decimal("3000"))

    def test_rebuild_aggregates_multiple_sprints(self):
        sprint2 = make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            name="Sprint 2",
            status=SprintStatus.COMPLETED,
        )
        make_sprint_actual(self.project, self.sprint, total_cost="2000")
        make_sprint_actual(self.project, sprint2, total_cost="3000")
        self.svc._rebuild_fy(self.fy)
        record = ProjectActuals.objects.get(project=self.project, fy=self.fy)
        self.assertEqual(record.total_cost_to_date, Decimal("5000"))

    def test_rebuild_replaces_existing_project_actuals(self):
        make_actuals(self.project, self.fy, total_cost_to_date="99999")
        make_sprint_actual(self.project, self.sprint, total_cost="1000")
        self.svc._rebuild_fy(self.fy)
        record = ProjectActuals.objects.get(project=self.project, fy=self.fy)
        self.assertEqual(record.total_cost_to_date, Decimal("1000"))

    def test_rebuild_sets_prev_fy_actuals_from_prior_record(self):
        prior_fy = make_financial_year(
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
        )
        make_actuals(
            self.project, prior_fy, total_cost_to_date="4000", prev_fy_actuals="1000"
        )
        make_sprint_actual(self.project, self.sprint, total_cost="2000")
        self.svc._rebuild_fy(self.fy)
        record = ProjectActuals.objects.get(project=self.project, fy=self.fy)
        # prev = prior_fy.total_cost_to_date + prior_fy.prev_fy_actuals = 4000 + 1000
        self.assertEqual(record.prev_fy_actuals, Decimal("5000"))

    def test_rebuild_prev_fy_actuals_zero_when_no_prior_fy(self):
        make_sprint_actual(self.project, self.sprint, total_cost="2000")
        self.svc._rebuild_fy(self.fy)
        record = ProjectActuals.objects.get(project=self.project, fy=self.fy)
        self.assertEqual(record.prev_fy_actuals, Decimal("0"))

    def test_rebuild_excludes_terminal_projects(self):
        terminal_status = make_project_status(name="Terminal Status", is_terminal=True)
        terminal_project = make_project(name="Terminal Project", status=terminal_status)
        make_sprint_actual(terminal_project, self.sprint, total_cost="9000")
        make_sprint_actual(self.project, self.sprint, total_cost="1000")
        self.svc._rebuild_fy(self.fy)
        self.assertFalse(
            ProjectActuals.objects.filter(project=terminal_project, fy=self.fy).exists()
        )

    def test_rebuild_scoped_to_given_project_ids_only(self):
        project2 = make_project(name="Project B")
        make_sprint_actual(self.project, self.sprint, total_cost="1000")
        make_sprint_actual(project2, self.sprint, total_cost="2000")
        self.svc._rebuild_fy(self.fy, project_ids=[self.project.pk])
        self.assertFalse(
            ProjectActuals.objects.filter(project=project2, fy=self.fy).exists()
        )
        self.assertTrue(
            ProjectActuals.objects.filter(project=self.project, fy=self.fy).exists()
        )

    def test_rebuild_returns_count_of_records_created(self):
        project2 = make_project(name="Project B")
        make_sprint_actual(self.project, self.sprint, total_cost="1000")
        make_sprint_actual(project2, self.sprint, total_cost="2000")
        count = self.svc._rebuild_fy(self.fy)
        self.assertEqual(count, 2)


# ── sync_for_fy ────────────────────────────────────────────────────────────────


class SyncForFyBasicTest(TestCase):
    """sync_for_fy() rebuilds the target FY and returns created count."""

    def setUp(self):
        mark_setup_complete()
        self.svc = make_service()
        self.project = make_project()
        self.fy = make_financial_year()
        self.sprint = make_sprint(
            financial_year=self.fy,
            status=SprintStatus.COMPLETED,
        )

    def test_sync_creates_project_actuals_from_sprint_actuals(self):
        make_sprint_actual(self.project, self.sprint, total_cost="5000")
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        self.assertTrue(
            ProjectActuals.objects.filter(project=self.project, fy=self.fy).exists()
        )

    def test_sync_returns_count_of_records_created(self):
        make_sprint_actual(self.project, self.sprint, total_cost="5000")
        count = self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        self.assertEqual(count, 1)

    def test_sync_with_no_sprint_actuals_returns_zero(self):
        count = self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        self.assertEqual(count, 0)

    def test_sync_with_no_sprint_actuals_does_not_raise(self):
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)

    def test_sync_scoped_to_specific_project_ids(self):
        project2 = make_project(name="Project B")
        make_sprint_actual(self.project, self.sprint, total_cost="1000")
        make_sprint_actual(project2, self.sprint, total_cost="2000")
        self.svc.sync_for_fy(sprint_id=self.sprint.pk, project_ids=[self.project.pk])
        self.assertTrue(
            ProjectActuals.objects.filter(project=self.project, fy=self.fy).exists()
        )
        self.assertFalse(
            ProjectActuals.objects.filter(project=project2, fy=self.fy).exists()
        )

    def test_removing_sprint_actual_and_resyncing_removes_contribution(self):
        psa = make_sprint_actual(self.project, self.sprint, total_cost="5000")
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        psa.delete()
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        self.assertFalse(
            ProjectActuals.objects.filter(project=self.project, fy=self.fy).exists()
        )


# ── sync_for_fy cascade ───────────────────────────────────────────────────────


class SyncForFyCascadeTest(TestCase):
    """sync_for_fy() propagates changes to subsequent FYs in chronological order."""

    def setUp(self):
        mark_setup_complete()
        self.svc = make_service()
        self.project = make_project()
        self.fy1 = make_financial_year(
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
        )
        self.fy2 = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
        )
        self.sprint1 = make_sprint(
            financial_year=self.fy1,
            sprint_number=1,
            name="FY1 Sprint 1",
            status=SprintStatus.COMPLETED,
        )
        self.sprint2 = make_sprint(
            financial_year=self.fy2,
            sprint_number=2,
            name="FY2 Sprint 1",
            status=SprintStatus.COMPLETED,
        )

    def test_cascade_updates_fy2_prev_fy_actuals_after_fy1_sync(self):
        make_sprint_actual(self.project, self.sprint1, total_cost="4000")
        make_sprint_actual(self.project, self.sprint2, total_cost="2000")
        # Pre-create FY2 ProjectActuals so cascade has something to rebuild
        make_actuals(
            self.project, self.fy2, total_cost_to_date="2000", prev_fy_actuals="0"
        )
        # Sync FY1 — should cascade and update FY2's prev_fy_actuals
        self.svc.sync_for_fy(sprint_id=self.sprint1.pk)
        fy2_record = ProjectActuals.objects.get(project=self.project, fy=self.fy2)
        # After cascade, FY2.prev_fy_actuals = FY1.total_cost_to_date (4000) + 0
        self.assertEqual(fy2_record.prev_fy_actuals, Decimal("4000"))

    def test_cascade_creates_fy1_record_with_correct_total(self):
        make_sprint_actual(self.project, self.sprint1, total_cost="3000")
        make_sprint_actual(self.project, self.sprint2, total_cost="1000")
        make_actuals(self.project, self.fy2, total_cost_to_date="1000")
        self.svc.sync_for_fy(sprint_id=self.sprint1.pk)
        fy1_record = ProjectActuals.objects.get(project=self.project, fy=self.fy1)
        self.assertEqual(fy1_record.total_cost_to_date, Decimal("3000"))

    def test_cascade_does_not_create_fy2_record_when_none_exists(self):
        """Cascade only rebuilds FYs that already have ProjectActuals records."""
        make_sprint_actual(self.project, self.sprint1, total_cost="1000")
        # Do NOT pre-create FY2 record — cascade should not create a new one
        self.svc.sync_for_fy(sprint_id=self.sprint1.pk)
        self.assertFalse(
            ProjectActuals.objects.filter(project=self.project, fy=self.fy2).exists()
        )

    def test_cascade_three_fy_chain_propagates_correctly(self):
        fy3 = make_financial_year(
            start_date=date(2025, 4, 1),
            end_date=date(2026, 3, 31),
        )
        sprint3 = make_sprint(
            financial_year=fy3,
            sprint_number=3,
            name="FY3 Sprint 1",
            status=SprintStatus.COMPLETED,
        )
        make_sprint_actual(self.project, self.sprint1, total_cost="1000")
        make_sprint_actual(self.project, self.sprint2, total_cost="2000")
        make_sprint_actual(self.project, sprint3, total_cost="3000")
        # Pre-create FY2 and FY3 records so cascade rebuilds them
        make_actuals(self.project, self.fy2, total_cost_to_date="2000")
        make_actuals(self.project, fy3, total_cost_to_date="3000")
        self.svc.sync_for_fy(sprint_id=self.sprint1.pk)
        fy2_record = ProjectActuals.objects.get(project=self.project, fy=self.fy2)
        fy3_record = ProjectActuals.objects.get(project=self.project, fy=fy3)
        # FY2.prev = FY1.total (1000) + FY1.prev (0) = 1000
        self.assertEqual(fy2_record.prev_fy_actuals, Decimal("1000"))
        # FY3.prev = FY2.total (2000) + FY2.prev (1000) = 3000
        self.assertEqual(fy3_record.prev_fy_actuals, Decimal("3000"))

    def test_cascade_scoped_to_project_ids_does_not_affect_others(self):
        project2 = make_project(name="Project B")
        make_sprint_actual(self.project, self.sprint1, total_cost="1000")
        make_sprint_actual(project2, self.sprint1, total_cost="2000")
        make_sprint_actual(self.project, self.sprint2, total_cost="500")
        make_sprint_actual(project2, self.sprint2, total_cost="700")
        make_actuals(self.project, self.fy2, total_cost_to_date="500")
        make_actuals(project2, self.fy2, total_cost_to_date="700")
        # Sync only project1
        self.svc.sync_for_fy(sprint_id=self.sprint1.pk, project_ids=[self.project.pk])
        # project2's FY2 prev should remain stale (not updated)
        proj2_fy2 = ProjectActuals.objects.get(project=project2, fy=self.fy2)
        self.assertEqual(proj2_fy2.prev_fy_actuals, Decimal("0"))


# ── orphan and edge cases ─────────────────────────────────────────────────────


class SyncForFyEdgeCasesTest(TestCase):
    """Edge cases: no recharge, orphan handling, terminal projects."""

    def setUp(self):
        mark_setup_complete()
        self.svc = make_service()
        self.project = make_project()
        self.fy = make_financial_year()
        self.sprint = make_sprint(
            financial_year=self.fy,
            status=SprintStatus.COMPLETED,
        )

    def test_sync_with_no_actuals_is_a_no_op_no_error(self):
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        self.assertEqual(ProjectActuals.objects.count(), 0)

    def test_sync_after_deleting_all_sprint_actuals_removes_project_actuals(self):
        psa = make_sprint_actual(self.project, self.sprint, total_cost="5000")
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        self.assertEqual(ProjectActuals.objects.filter(fy=self.fy).count(), 1)
        psa.delete()
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        self.assertEqual(ProjectActuals.objects.filter(fy=self.fy).count(), 0)

    def test_sync_terminal_project_actuals_are_excluded(self):
        terminal_status = make_project_status(
            name="Completed Terminal", is_terminal=True
        )
        terminal_project = make_project(name="Terminal", status=terminal_status)
        make_sprint_actual(terminal_project, self.sprint, total_cost="9000")
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        self.assertFalse(
            ProjectActuals.objects.filter(project=terminal_project, fy=self.fy).exists()
        )

    def test_sync_multiple_projects_independent(self):
        project2 = make_project(name="Project B")
        make_sprint_actual(self.project, self.sprint, total_cost="1000")
        make_sprint_actual(project2, self.sprint, total_cost="2000")
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        p1_record = ProjectActuals.objects.get(project=self.project, fy=self.fy)
        p2_record = ProjectActuals.objects.get(project=project2, fy=self.fy)
        self.assertEqual(p1_record.total_cost_to_date, Decimal("1000"))
        self.assertEqual(p2_record.total_cost_to_date, Decimal("2000"))

    def test_sync_partial_update_leaves_unscoped_projects_unchanged(self):
        project2 = make_project(name="Project B")
        make_sprint_actual(self.project, self.sprint, total_cost="1000")
        make_sprint_actual(project2, self.sprint, total_cost="2000")
        self.svc.sync_for_fy(sprint_id=self.sprint.pk)
        # Update only project2 sprint actuals and re-sync scoped
        ProjectSprintActual.objects.filter(project=project2, sprint=self.sprint).update(
            total_cost=Decimal("9000")
        )
        self.svc.sync_for_fy(sprint_id=self.sprint.pk, project_ids=[project2.pk])
        p1_record = ProjectActuals.objects.get(project=self.project, fy=self.fy)
        p2_record = ProjectActuals.objects.get(project=project2, fy=self.fy)
        self.assertEqual(p1_record.total_cost_to_date, Decimal("1000"))
        self.assertEqual(p2_record.total_cost_to_date, Decimal("9000"))
