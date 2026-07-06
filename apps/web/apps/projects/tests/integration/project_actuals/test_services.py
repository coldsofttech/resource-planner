from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.constants import ProjectEstimateStatus
from apps.projects.models import ProjectActuals
from apps.projects.models.project_actual_config import ProjectActualConfig
from apps.projects.models.project_sprint_actual import ProjectSprintActual
from apps.projects.services.project_actuals import ProjectActualsService
from apps.projects.tests.factories import (
    make_estimate,
    make_financial_year,
    make_project,
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


# ------------------------------------------------------------------ #
# summary() — config-aware totals                                      #
# ------------------------------------------------------------------ #


class ProjectActualsServiceSummaryTableTest(TestCase):
    """summary() returns correct fields and ignores prev_fy_actuals when configured."""

    def setUp(self):
        mark_setup_complete()
        self.project = make_project()
        self.fy = make_financial_year()
        self.svc = make_service()
        # Approved estimate: 20 days × £1 000 = £20 000 base, 0 % contingency
        make_estimate(
            project=self.project,
            estimate_days=20,
            day_rate=1000,
            contingency_percentage=0,
            status=ProjectEstimateStatus.APPROVED,
        )

    def test_summary_returns_expected_keys(self):
        make_actuals(self.project, self.fy, total_cost_to_date="8000")
        result = self.svc.summary(project_code=self.project.code)
        for key in (
            "estimate_cost",
            "estimate_cost_with_contingency",
            "total_actuals",
            "remaining_amount",
            "risk",
        ):
            self.assertIn(key, result)

    def test_total_actuals_includes_prev_fy_by_default(self):
        make_actuals(
            self.project, self.fy, total_cost_to_date="8000", prev_fy_actuals="5000"
        )
        result = self.svc.summary(project_code=self.project.code)
        self.assertAlmostEqual(result["total_actuals"], 13_000.0)

    def test_ignore_prev_fy_actuals_excludes_prior_year(self):
        ProjectActualConfig.objects.create(
            project=self.project, ignore_prev_fy_actuals=True
        )
        make_actuals(
            self.project, self.fy, total_cost_to_date="8000", prev_fy_actuals="5000"
        )
        result = self.svc.summary(project_code=self.project.code)
        self.assertAlmostEqual(result["total_actuals"], 8_000.0)

    def test_remaining_amount_none_when_no_estimate(self):
        project2 = make_project(name="No Estimate Project")
        result = self.svc.summary(project_code=project2.code)
        self.assertIsNone(result["remaining_amount"])

    def test_remaining_amount_computed_from_estimate_cost(self):
        make_actuals(self.project, self.fy, total_cost_to_date="6000")
        result = self.svc.summary(project_code=self.project.code)
        self.assertAlmostEqual(result["remaining_amount"], 14_000.0)

    def test_risk_is_none_when_no_actuals_exist(self):
        result = self.svc.summary(project_code=self.project.code)
        self.assertIsNone(result["risk"])

    def test_risk_is_at_risk_when_actuals_exceed_contingency(self):
        make_estimate(
            project=self.project,
            version=2,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        make_actuals(self.project, self.fy, total_cost_to_date="12000")
        result = self.svc.summary(project_code=self.project.code)
        self.assertEqual(result["risk"], "at_risk")

    def test_risk_suppressed_by_ignore_risk_config(self):
        ProjectActualConfig.objects.create(project=self.project, ignore_risk=True)
        make_actuals(self.project, self.fy, total_cost_to_date="50000")
        result = self.svc.summary(project_code=self.project.code)
        self.assertIsNone(result["risk"])


# ------------------------------------------------------------------ #
# table_data() — by-FY mode                                            #
# ------------------------------------------------------------------ #


class ProjectActualsServiceTableDataFyModeTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.project = make_project()
        self.svc = make_service()

    def test_returns_empty_list_when_no_actuals(self):
        result = self.svc.table_data(project_code=self.project.code)
        self.assertEqual(result, [])

    def test_single_fy_row_fields(self):
        fy = make_financial_year()
        make_actuals(self.project, fy, total_cost_to_date="8000", prev_fy_actuals="0")
        result = self.svc.table_data(project_code=self.project.code)
        self.assertEqual(len(result), 1)
        row = result[0]
        for key in ("fy", "fy_code", "total_days", "total_cost", "cumulative_cost"):
            self.assertIn(key, row)

    def test_cumulative_cost_is_total_plus_prev(self):
        fy = make_financial_year()
        make_actuals(
            self.project, fy, total_cost_to_date="8000", prev_fy_actuals="5000"
        )
        result = self.svc.table_data(project_code=self.project.code)
        self.assertAlmostEqual(result[0]["cumulative_cost"], 13_000.0)
        self.assertAlmostEqual(result[0]["total_cost"], 8_000.0)

    def test_multiple_fy_rows_ordered_by_start_date(self):
        fy1 = make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_actuals(self.project, fy1, total_cost_to_date="5000")
        make_actuals(
            self.project, fy2, total_cost_to_date="3000", prev_fy_actuals="5000"
        )
        result = self.svc.table_data(project_code=self.project.code)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["fy_code"], fy1.code)
        self.assertEqual(result[1]["fy_code"], fy2.code)
        self.assertAlmostEqual(result[1]["cumulative_cost"], 8_000.0)

    def test_total_days_aggregated_from_sprint_actuals(self):
        fy = make_financial_year()
        sprint = make_sprint(financial_year=fy, status=SprintStatus.COMPLETED)
        ProjectSprintActual.objects.create(
            project=self.project,
            sprint=sprint,
            total_days=Decimal("5"),
            total_cost=Decimal("5000"),
        )
        make_actuals(self.project, fy, total_cost_to_date="5000")
        result = self.svc.table_data(project_code=self.project.code)
        self.assertAlmostEqual(result[0]["total_days"], 5.0)

    def test_404_for_unknown_project_code(self):
        from apps.core.exceptions import NotFoundException

        with self.assertRaises(NotFoundException):
            self.svc.table_data(project_code="PROJ-NONE")


# ------------------------------------------------------------------ #
# table_data() — by-sprint mode (fy_code provided)                    #
# ------------------------------------------------------------------ #


class ProjectActualsServiceTableDataSprintModeTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.project = make_project()
        self.fy = make_financial_year()
        self.svc = make_service()

    def test_returns_empty_list_when_no_non_future_sprints(self):
        make_sprint(financial_year=self.fy, status=SprintStatus.FUTURE)
        result = self.svc.table_data(
            project_code=self.project.code, fy_code=self.fy.code
        )
        self.assertEqual(result, [])

    def test_sprint_row_contains_expected_fields(self):
        make_sprint(financial_year=self.fy, status=SprintStatus.COMPLETED)
        result = self.svc.table_data(
            project_code=self.project.code, fy_code=self.fy.code
        )
        self.assertEqual(len(result), 1)
        row = result[0]
        for key in (
            "sprint",
            "sprint_number",
            "total_days",
            "total_cost",
            "cumulative_cost",
        ):
            self.assertIn(key, row)

    def test_sprint_with_no_actuals_has_zero_values(self):
        make_sprint(financial_year=self.fy, status=SprintStatus.COMPLETED)
        result = self.svc.table_data(
            project_code=self.project.code, fy_code=self.fy.code
        )
        self.assertEqual(result[0]["total_cost"], 0.0)
        self.assertEqual(result[0]["total_days"], 0.0)
        self.assertEqual(result[0]["cumulative_cost"], 0.0)

    def test_sprint_rows_ordered_by_sprint_number(self):
        s1 = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            name="Sprint 1",
            status=SprintStatus.COMPLETED,
        )
        s2 = make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            name="Sprint 2",
            status=SprintStatus.COMPLETED,
        )
        ProjectSprintActual.objects.create(
            project=self.project,
            sprint=s2,
            total_days=Decimal("2"),
            total_cost=Decimal("2000"),
        )
        ProjectSprintActual.objects.create(
            project=self.project,
            sprint=s1,
            total_days=Decimal("3"),
            total_cost=Decimal("3000"),
        )
        result = self.svc.table_data(
            project_code=self.project.code, fy_code=self.fy.code
        )
        self.assertEqual(result[0]["sprint_number"], 1)
        self.assertEqual(result[1]["sprint_number"], 2)

    def test_cumulative_cost_carries_forward_across_zero_actuals_sprint(self):
        s1 = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            name="Sprint 1",
            status=SprintStatus.COMPLETED,
        )
        make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            name="Sprint 2",
            status=SprintStatus.COMPLETED,
        )
        s3 = make_sprint(
            financial_year=self.fy,
            sprint_number=3,
            name="Sprint 3",
            status=SprintStatus.COMPLETED,
        )
        ProjectSprintActual.objects.create(
            project=self.project,
            sprint=s1,
            total_days=Decimal("1"),
            total_cost=Decimal("1000"),
        )
        # s2 has no actuals — should carry forward £1 000 cumulative
        ProjectSprintActual.objects.create(
            project=self.project,
            sprint=s3,
            total_days=Decimal("1"),
            total_cost=Decimal("2000"),
        )
        result = self.svc.table_data(
            project_code=self.project.code, fy_code=self.fy.code
        )
        self.assertEqual(result[0]["cumulative_cost"], 1000.0)
        self.assertEqual(result[1]["cumulative_cost"], 1000.0)
        self.assertEqual(result[2]["cumulative_cost"], 3000.0)

    def test_future_sprints_excluded_from_drill_down(self):
        make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            name="Sprint 1",
            status=SprintStatus.COMPLETED,
        )
        make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            name="Sprint 2",
            status=SprintStatus.FUTURE,
        )
        result = self.svc.table_data(
            project_code=self.project.code, fy_code=self.fy.code
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sprint"], "Sprint 1")
