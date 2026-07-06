from decimal import Decimal

from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.constants import ActualsRiskType, ProjectEstimateStatus
from apps.projects.models import ProjectActuals
from apps.projects.models.project_actual_config import ProjectActualConfig
from apps.projects.models.project_sprint_actual import ProjectSprintActual
from apps.projects.tests.factories import (
    make_estimate,
    make_financial_year,
    make_project,
)
from apps.sprints.constants import SprintStatus
from apps.sprints.tests.factories import make_sprint


def make_actuals(project, fy, total_cost_to_date="0", prev_fy_actuals="0"):
    return ProjectActuals.objects.create(
        project=project,
        fy=fy,
        total_cost_to_date=Decimal(total_cost_to_date),
        prev_fy_actuals=Decimal(prev_fy_actuals),
    )


# ------------------------------------------------------------------ #
# remaining_amount property                                            #
# ------------------------------------------------------------------ #


class ProjectActualsRemainingAmountTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.project = make_project()
        self.fy = make_financial_year()

    def test_returns_none_when_no_approved_estimate(self):
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="5000")
        self.assertIsNone(actuals.remaining_amount)

    def test_base_path_actuals_within_base_cost(self):
        # estimate: 10 days × £1 000 = £10 000 base, 0 % contingency
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=0,
            status=ProjectEstimateStatus.APPROVED,
        )
        # actuals £6 000 — within base → remaining = £10 000 − £6 000 = £4 000
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="6000")
        self.assertEqual(actuals.remaining_amount, Decimal("4000"))

    def test_contingency_path_actuals_exceed_base_but_within_contingency(self):
        # 10 days × £1 000 = £10 000 base + 20 % = £12 000 with contingency
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=20,
            status=ProjectEstimateStatus.APPROVED,
        )
        # actuals £11 000 — above base,
        # within contingency → remaining = £12 000 − £11 000 = £1 000
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="11000")
        self.assertEqual(actuals.remaining_amount, Decimal("1000"))

    def test_negative_remaining_when_actuals_exceed_contingency(self):
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        # base = £10 000, with contingency = £11 000;
        # actuals £13 000 → remaining = −£2 000
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="13000")
        self.assertEqual(actuals.remaining_amount, Decimal("-2000"))

    def test_prev_fy_actuals_included_in_total_by_default(self):
        make_estimate(
            project=self.project,
            estimate_days=20,
            day_rate=1000,
            contingency_percentage=0,
            status=ProjectEstimateStatus.APPROVED,
        )
        # base = £20 000; current FY £8 000 + prev £5 000 = £13 000
        # total → remaining = £7 000
        actuals = make_actuals(
            self.project, self.fy, total_cost_to_date="8000", prev_fy_actuals="5000"
        )
        self.assertEqual(actuals.remaining_amount, Decimal("7000"))

    def test_ignore_prev_fy_actuals_excludes_prior_year_cost(self):
        make_estimate(
            project=self.project,
            estimate_days=20,
            day_rate=1000,
            contingency_percentage=0,
            status=ProjectEstimateStatus.APPROVED,
        )
        ProjectActualConfig.objects.create(
            project=self.project, ignore_prev_fy_actuals=True
        )
        # With flag set, only £8 000 counts → remaining = £20 000 − £8 000 = £12 000
        actuals = make_actuals(
            self.project, self.fy, total_cost_to_date="8000", prev_fy_actuals="5000"
        )
        self.assertEqual(actuals.remaining_amount, Decimal("12000"))


# ------------------------------------------------------------------ #
# risk property                                                        #
# ------------------------------------------------------------------ #


class ProjectActualsRiskTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.project = make_project()
        self.fy = make_financial_year()

    def test_returns_none_when_no_approved_estimate(self):
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="99000")
        self.assertIsNone(actuals.risk)

    def test_returns_none_when_actuals_within_base_cost(self):
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="9000")
        self.assertIsNone(actuals.risk)

    def test_returns_warning_when_actuals_between_base_and_contingency(self):
        # base = £10 000, with 10 % contingency = £11 000
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="10500")
        self.assertEqual(actuals.risk, ActualsRiskType.WARNING)

    def test_returns_at_risk_when_actuals_exceed_contingency(self):
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="12000")
        self.assertEqual(actuals.risk, ActualsRiskType.AT_RISK)

    def test_ignore_risk_config_suppresses_risk(self):
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        ProjectActualConfig.objects.create(project=self.project, ignore_risk=True)
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="15000")
        self.assertIsNone(actuals.risk)

    def test_zero_base_cost_estimate_returns_none(self):
        # estimate_days=0 → base=0 → risk cannot be calculated
        make_estimate(
            project=self.project,
            estimate_days=0,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        actuals = make_actuals(self.project, self.fy, total_cost_to_date="1000")
        self.assertIsNone(actuals.risk)

    def test_prev_fy_actuals_contribute_to_risk(self):
        # base = £10 000; current FY £5 000 + prev £6 000 = £11 000
        # (over base but with contingency=10% → £11 000 exactly on boundary)
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        # total = £11 001 → at risk
        actuals = make_actuals(
            self.project, self.fy, total_cost_to_date="5001", prev_fy_actuals="6000"
        )
        self.assertEqual(actuals.risk, ActualsRiskType.AT_RISK)


# ------------------------------------------------------------------ #
# _sprint_rows (via ProjectSprintActual, zero-fill & cumulative)      #
# ------------------------------------------------------------------ #


class ProjectSprintActualZeroFillTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.project = make_project()
        self.fy = make_financial_year()

    def _make_sprint_actual(self, sprint, total_days="1", total_cost="500"):
        return ProjectSprintActual.objects.create(
            project=self.project,
            sprint=sprint,
            total_days=Decimal(total_days),
            total_cost=Decimal(total_cost),
        )

    def test_sprint_with_no_actuals_has_zero_cost(self):
        make_sprint(financial_year=self.fy, status=SprintStatus.COMPLETED)
        from apps.projects.services.project_actuals import ProjectActualsService

        svc = ProjectActualsService()
        rows = svc._sprint_rows(self.project, self.fy.code)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["total_cost"], 0.0)
        self.assertEqual(rows[0]["total_days"], 0.0)
        self.assertEqual(rows[0]["cumulative_cost"], 0.0)

    def test_future_sprints_are_excluded(self):
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
        from apps.projects.services.project_actuals import ProjectActualsService

        svc = ProjectActualsService()
        rows = svc._sprint_rows(self.project, self.fy.code)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sprint"], "Sprint 1")

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
        # Sprint 1 costs £1 000, Sprint 2 has no actuals (zero-fill),
        # Sprint 3 costs £2 000
        self._make_sprint_actual(s1, total_cost="1000")
        self._make_sprint_actual(s3, total_cost="2000")

        from apps.projects.services.project_actuals import ProjectActualsService

        svc = ProjectActualsService()
        rows = svc._sprint_rows(self.project, self.fy.code)

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["total_cost"], 1000.0)
        self.assertEqual(rows[0]["cumulative_cost"], 1000.0)
        self.assertEqual(rows[1]["total_cost"], 0.0)
        self.assertEqual(rows[1]["cumulative_cost"], 1000.0)  # carry-forward
        self.assertEqual(rows[2]["total_cost"], 2000.0)
        self.assertEqual(rows[2]["cumulative_cost"], 3000.0)

    def test_empty_fy_returns_empty_list(self):
        from apps.projects.services.project_actuals import ProjectActualsService

        svc = ProjectActualsService()
        rows = svc._sprint_rows(self.project, self.fy.code)
        self.assertEqual(rows, [])
