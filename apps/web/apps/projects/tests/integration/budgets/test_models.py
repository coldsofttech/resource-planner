from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectBudget
from apps.projects.tests.factories import (
    make_budget,
    make_estimate,
    make_financial_year,
    make_project,
)


class ProjectBudgetFieldDefaultsTest(TestCase):
    def test_allocated_budget_defaults_to_zero(self):
        fy = make_financial_year()
        project = make_project()
        budget = ProjectBudget.objects.create(
            project=project,
            financial_year=fy,
        )
        self.assertEqual(budget.allocated_budget, Decimal("0"))

    def test_refined_budget_defaults_to_none(self):
        budget = make_budget()
        self.assertIsNone(budget.refined_budget)

    def test_estimate_version_defaults_to_none(self):
        budget = make_budget()
        self.assertIsNone(budget.estimate_version)

    def test_note_defaults_to_empty_string(self):
        budget = make_budget()
        self.assertEqual(budget.note, "")

    def test_created_by_defaults_to_none(self):
        budget = make_budget()
        self.assertIsNone(budget.created_by)

    def test_updated_by_defaults_to_none(self):
        budget = make_budget()
        self.assertIsNone(budget.updated_by)

    def test_created_at_auto_set(self):
        budget = make_budget()
        self.assertIsNotNone(budget.created_at)

    def test_updated_at_auto_set(self):
        budget = make_budget()
        self.assertIsNotNone(budget.updated_at)

    def test_code_auto_generated(self):
        budget = make_budget()
        self.assertTrue(budget.code.startswith("PROJBGT-"))


class ProjectBudgetUniqueConstraintTest(TestCase):
    def test_duplicate_project_and_financial_year_raises_integrity_error(self):
        project = make_project()
        fy = make_financial_year()
        make_budget(project=project, financial_year=fy)
        with self.assertRaises(IntegrityError):
            make_budget(project=project, financial_year=fy)

    def test_same_project_different_financial_year_is_allowed(self):
        from datetime import date

        project = make_project()
        fy1 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        b1 = make_budget(project=project, financial_year=fy1)
        b2 = make_budget(project=project, financial_year=fy2)
        self.assertNotEqual(b1.pk, b2.pk)

    def test_same_financial_year_different_project_is_allowed(self):
        fy = make_financial_year()
        p1 = make_project(name="Project A")
        p2 = make_project(name="Project B")
        b1 = make_budget(project=p1, financial_year=fy)
        b2 = make_budget(project=p2, financial_year=fy)
        self.assertNotEqual(b1.pk, b2.pk)


class ProjectBudgetActualBudgetPropertyTest(TestCase):
    def test_actual_budget_uses_allocated_when_refined_is_none(self):
        budget = make_budget(allocated_budget=100_000, refined_budget=None)
        self.assertEqual(budget.actual_budget, 100_000.0)

    def test_actual_budget_uses_refined_when_set(self):
        budget = make_budget(
            allocated_budget=100_000, refined_budget=Decimal("90000.00")
        )
        self.assertEqual(budget.actual_budget, 90_000.0)

    def test_actual_budget_returns_float(self):
        budget = make_budget(allocated_budget=50_000)
        self.assertIsInstance(budget.actual_budget, float)


class ProjectBudgetRemainingBudgetPropertyTest(TestCase):
    def test_remaining_budget_equals_actual_when_no_estimate(self):
        budget = make_budget(allocated_budget=100_000, refined_budget=None)
        self.assertEqual(budget.remaining_budget, 100_000.0)

    def test_remaining_budget_computed_when_estimate_exists(self):
        estimate = make_estimate(
            estimate_days=10, day_rate=1000, contingency_percentage=0
        )
        budget = make_budget(
            project=estimate.project,
            allocated_budget=100_000,
            estimate_version=estimate,
        )
        expected = round(100_000.0 - float(estimate.total_cost), 2)
        self.assertEqual(budget.remaining_budget, expected)

    def test_remaining_budget_can_be_negative_when_over_budget(self):
        estimate = make_estimate(
            estimate_days=200, day_rate=1000, contingency_percentage=0
        )
        budget = make_budget(
            project=estimate.project,
            allocated_budget=50_000,
            estimate_version=estimate,
        )
        self.assertLess(budget.remaining_budget, 0)


class ProjectBudgetRiskPropertyTest(TestCase):
    def setUp(self):
        mark_setup_complete()

    def test_risk_is_none_when_no_estimate_version(self):
        budget = make_budget(allocated_budget=100_000, refined_budget=None)
        self.assertIsNone(budget.risk)

    def test_risk_is_none_when_estimate_has_zero_cost(self):
        estimate = make_estimate(estimate_days=0, day_rate=0, contingency_percentage=0)
        budget = make_budget(
            project=estimate.project,
            allocated_budget=100_000,
            estimate_version=estimate,
        )
        self.assertIsNone(budget.risk)

    def test_risk_returns_dict_when_estimate_exists_and_non_zero(self):
        estimate = make_estimate(
            estimate_days=10, day_rate=1000, contingency_percentage=0
        )
        budget = make_budget(
            project=estimate.project,
            allocated_budget=100_000,
            estimate_version=estimate,
        )
        risk = budget.risk
        self.assertIsNotNone(risk)
        self.assertIn("color", risk)
        self.assertIn("display", risk)
        self.assertIn("short", risk)
        self.assertIn("percentage", risk)

    def test_risk_color_values_are_valid(self):
        estimate = make_estimate(
            estimate_days=10, day_rate=1000, contingency_percentage=0
        )
        budget = make_budget(
            project=estimate.project,
            allocated_budget=100_000,
            estimate_version=estimate,
        )
        risk = budget.risk
        self.assertIn(risk["color"], ["GREEN", "AMBER", "RED"])
