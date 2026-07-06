from decimal import Decimal

from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.core.exceptions import NotFoundException
from apps.financial_years.models import FinancialYear
from apps.projects.constants import ProjectEstimateStatus
from apps.projects.models import ProjectActuals
from apps.projects.models.project_actual_config import ProjectActualConfig
from apps.projects.services.project_actuals import ProjectActualsService
from apps.projects.tests.factories import (
    make_estimate,
    make_financial_year,
    make_project,
)
from apps.users.tests.factories import make_user


def make_service(user=None):
    svc = ProjectActualsService()
    svc.user = user or make_user()
    return svc


def make_project_actuals(
    project,
    fy: FinancialYear,
    total_cost_to_date: Decimal = Decimal("0"),
    prev_fy_actuals: Decimal = Decimal("0"),
) -> ProjectActuals:
    return ProjectActuals.objects.create(
        project=project,
        fy=fy,
        total_cost_to_date=total_cost_to_date,
        prev_fy_actuals=prev_fy_actuals,
    )


class ProjectActualsServiceGetConfigTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.project = make_project()
        self.svc = make_service()

    def test_returns_defaults_when_no_config_exists(self):
        result = self.svc.get_config(project_code=self.project.code)
        self.assertFalse(result["ignore_risk"])
        self.assertFalse(result["ignore_prev_fy_actuals"])
        self.assertEqual(result["notes"], "")

    def test_returns_persisted_values_when_config_exists(self):
        ProjectActualConfig.objects.create(
            project=self.project,
            ignore_risk=True,
            ignore_prev_fy_actuals=True,
            notes="Carry-over note.",
        )
        result = self.svc.get_config(project_code=self.project.code)
        self.assertTrue(result["ignore_risk"])
        self.assertTrue(result["ignore_prev_fy_actuals"])
        self.assertEqual(result["notes"], "Carry-over note.")

    def test_raises_not_found_for_unknown_project_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get_config(project_code="PROJ-DOES-NOT-EXIST")


class ProjectActualsServiceUpdateConfigTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.project = make_project()
        self.svc = make_service()

    def test_creates_config_on_first_call(self):
        self.assertFalse(
            ProjectActualConfig.objects.filter(project=self.project).exists()
        )
        self.svc.update_config(project_code=self.project.code, ignore_risk=True)
        self.assertTrue(
            ProjectActualConfig.objects.filter(project=self.project).exists()
        )

    def test_returns_updated_values_after_create(self):
        result = self.svc.update_config(
            project_code=self.project.code,
            ignore_risk=True,
            ignore_prev_fy_actuals=False,
            notes="First save.",
        )
        self.assertTrue(result["ignore_risk"])
        self.assertFalse(result["ignore_prev_fy_actuals"])
        self.assertEqual(result["notes"], "First save.")

    def test_updates_existing_config_on_subsequent_call(self):
        self.svc.update_config(
            project_code=self.project.code,
            ignore_risk=True,
            notes="Original.",
        )
        result = self.svc.update_config(
            project_code=self.project.code,
            ignore_risk=False,
            notes="Updated.",
        )
        self.assertFalse(result["ignore_risk"])
        self.assertEqual(result["notes"], "Updated.")

    def test_only_one_config_record_exists_after_multiple_updates(self):
        self.svc.update_config(project_code=self.project.code, ignore_risk=True)
        self.svc.update_config(project_code=self.project.code, ignore_risk=False)
        self.assertEqual(
            ProjectActualConfig.objects.filter(project=self.project).count(), 1
        )

    def test_partial_update_leaves_other_fields_unchanged(self):
        self.svc.update_config(
            project_code=self.project.code,
            ignore_risk=True,
            ignore_prev_fy_actuals=True,
            notes="Keep this.",
        )
        # Update only ignore_risk
        result = self.svc.update_config(
            project_code=self.project.code, ignore_risk=False
        )
        self.assertFalse(result["ignore_risk"])
        # Other fields remain as previously saved
        self.assertTrue(result["ignore_prev_fy_actuals"])
        self.assertEqual(result["notes"], "Keep this.")

    def test_raises_not_found_for_unknown_project_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update_config(project_code="PROJ-DOES-NOT-EXIST", ignore_risk=True)


class ProjectActualsServiceSummaryRiskTest(TestCase):
    """Tests that ignore_risk suppresses the risk field in summary()."""

    def setUp(self):
        mark_setup_complete()
        self.svc = make_service()
        # Approved estimate: 10 days × £1 000/day = £10 000 base
        # Contingency 10 % → £11 000 with contingency
        self.project = make_project()
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        self.fy = make_financial_year()
        # Total actuals £12 000 — exceeds contingency, so "at_risk" without config
        make_project_actuals(
            project=self.project,
            fy=self.fy,
            total_cost_to_date=Decimal("12000"),
            prev_fy_actuals=Decimal("0"),
        )

    def test_risk_is_at_risk_without_config(self):
        result = self.svc.summary(project_code=self.project.code)
        self.assertEqual(result["risk"], "at_risk")

    def test_ignore_risk_true_suppresses_risk_badge(self):
        ProjectActualConfig.objects.create(project=self.project, ignore_risk=True)
        result = self.svc.summary(project_code=self.project.code)
        self.assertIsNone(result["risk"])

    def test_ignore_risk_false_preserves_risk_badge(self):
        ProjectActualConfig.objects.create(project=self.project, ignore_risk=False)
        result = self.svc.summary(project_code=self.project.code)
        self.assertEqual(result["risk"], "at_risk")

    def test_risk_is_warning_when_actuals_between_estimate_and_contingency(self):
        # Overwrite actuals to £10 500 — above base but within contingency
        ProjectActuals.objects.filter(project=self.project).update(
            total_cost_to_date=Decimal("10500")
        )
        result = self.svc.summary(project_code=self.project.code)
        self.assertEqual(result["risk"], "warning")


class ProjectActualsServiceSummaryIgnorePrevFyTest(TestCase):
    """Tests that ignore_prev_fy_actuals excludes prev_fy_actuals from totals."""

    def setUp(self):
        mark_setup_complete()
        self.svc = make_service()
        self.project = make_project()
        make_estimate(
            project=self.project,
            estimate_days=20,
            day_rate=1000,
            contingency_percentage=0,
            status=ProjectEstimateStatus.APPROVED,
        )
        self.fy = make_financial_year()
        # Current FY cost £8 000, prior FY chain £5 000
        make_project_actuals(
            project=self.project,
            fy=self.fy,
            total_cost_to_date=Decimal("8000"),
            prev_fy_actuals=Decimal("5000"),
        )

    def test_total_actuals_includes_prev_fy_when_flag_is_false(self):
        result = self.svc.summary(project_code=self.project.code)
        # 8 000 + 5 000 = 13 000
        self.assertAlmostEqual(result["total_actuals"], 13_000.0)

    def test_ignore_prev_fy_actuals_true_excludes_prior_year_from_total(self):
        ProjectActualConfig.objects.create(
            project=self.project, ignore_prev_fy_actuals=True
        )
        result = self.svc.summary(project_code=self.project.code)
        # Only current FY cost: 8 000
        self.assertAlmostEqual(result["total_actuals"], 8_000.0)

    def test_remaining_amount_recalculates_with_ignore_prev_fy(self):
        ProjectActualConfig.objects.create(
            project=self.project, ignore_prev_fy_actuals=True
        )
        result = self.svc.summary(project_code=self.project.code)
        # estimate_cost = 20 000, total_actuals = 8 000 → remaining = 12 000
        self.assertAlmostEqual(result["remaining_amount"], 12_000.0)
