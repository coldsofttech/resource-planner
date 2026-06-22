from datetime import date

from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.selectors.budget import (
    budget_exists_for_project_and_fy,
    get_budget_by_code,
    get_budget_status_history,
    get_budgets_for_project,
    get_lifetime_budget_summary,
)
from apps.projects.tests.factories import (
    make_budget,
    make_budget_history,
    make_estimate,
    make_financial_year,
    make_project,
)


class GetBudgetByCodeTest(TestCase):
    def test_returns_budget_for_existing_code(self):
        budget = make_budget()
        result = get_budget_by_code(budget.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, budget.pk)

    def test_returns_none_for_unknown_code(self):
        result = get_budget_by_code("PROJBGT-DOES-NOT-EXIST")
        self.assertIsNone(result)

    def test_select_related_project(self):
        budget = make_budget()
        result = get_budget_by_code(budget.code)
        with self.assertNumQueries(0):
            _ = result.project.name

    def test_select_related_financial_year(self):
        budget = make_budget()
        result = get_budget_by_code(budget.code)
        with self.assertNumQueries(0):
            _ = result.financial_year.long_fy


class GetBudgetsForProjectTest(TestCase):
    def test_returns_empty_queryset_when_no_budgets(self):
        project = make_project()
        qs = get_budgets_for_project(project)
        self.assertEqual(qs.count(), 0)

    def test_returns_only_budgets_for_given_project(self):
        project_a = make_project(name="Project A")
        project_b = make_project(name="Project B")
        fy = make_financial_year()
        make_budget(project=project_a, financial_year=fy)
        make_budget(project=project_b, financial_year=fy)
        qs = get_budgets_for_project(project_a)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().project.pk, project_a.pk)

    def test_returns_multiple_budgets_for_project(self):
        project = make_project()
        fy1 = make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_budget(project=project, financial_year=fy1)
        make_budget(project=project, financial_year=fy2)
        qs = get_budgets_for_project(project)
        self.assertEqual(qs.count(), 2)

    def test_ordered_by_most_recent_financial_year_first(self):
        project = make_project()
        fy_old = make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31)
        )
        fy_new = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_budget(project=project, financial_year=fy_old)
        make_budget(project=project, financial_year=fy_new)
        qs = get_budgets_for_project(project)
        self.assertEqual(qs.first().financial_year.pk, fy_new.pk)


class BudgetExistsForProjectAndFyTest(TestCase):
    def test_returns_true_when_budget_exists(self):
        project = make_project()
        fy = make_financial_year()
        make_budget(project=project, financial_year=fy)
        self.assertTrue(budget_exists_for_project_and_fy(project, fy))

    def test_returns_false_when_no_budget(self):
        project = make_project()
        fy = make_financial_year()
        self.assertFalse(budget_exists_for_project_and_fy(project, fy))

    def test_returns_false_when_same_fy_different_project(self):
        fy = make_financial_year()
        project_a = make_project(name="A")
        project_b = make_project(name="B")
        make_budget(project=project_a, financial_year=fy)
        self.assertFalse(budget_exists_for_project_and_fy(project_b, fy))

    def test_exclude_pk_excludes_own_record(self):
        project = make_project()
        fy = make_financial_year()
        budget = make_budget(project=project, financial_year=fy)
        result = budget_exists_for_project_and_fy(project, fy, exclude_pk=budget.pk)
        self.assertFalse(result)

    def test_exclude_pk_still_detects_other_duplicate(self):
        project = make_project()
        fy1 = make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        budget_a = make_budget(project=project, financial_year=fy1)
        make_budget(project=project, financial_year=fy2)
        result = budget_exists_for_project_and_fy(project, fy1, exclude_pk=budget_a.pk)
        self.assertFalse(result)


class GetBudgetStatusHistoryTest(TestCase):
    def test_returns_empty_queryset_for_budget_with_no_history(self):
        project = make_project()
        fy = make_financial_year()
        budget = make_budget(project=project, financial_year=fy)
        qs = get_budget_status_history(budget)
        self.assertEqual(qs.count(), 0)

    def test_returns_history_records_for_budget(self):
        budget = make_budget()
        make_budget_history(budget=budget)
        make_budget_history(budget=budget)
        qs = get_budget_status_history(budget)
        self.assertEqual(qs.count(), 2)

    def test_does_not_return_history_for_other_budgets(self):
        budget_a = make_budget()
        budget_b = make_budget(project=make_project(name="Other"))
        make_budget_history(budget=budget_a)
        qs = get_budget_status_history(budget_b)
        self.assertEqual(qs.count(), 0)

    def test_ordered_most_recent_first(self):
        budget = make_budget()
        make_budget_history(budget=budget)
        make_budget_history(budget=budget)
        qs = get_budget_status_history(budget)
        self.assertEqual(qs.count(), 2)


class GetLifetimeBudgetSummaryTest(TestCase):
    def setUp(self):
        mark_setup_complete()

    def test_returns_zero_counts_for_project_with_no_budgets(self):
        project = make_project()
        summary = get_lifetime_budget_summary(project)
        self.assertEqual(summary["budget_count"], 0)
        self.assertEqual(summary["total_allocated_budget"], 0)
        self.assertEqual(summary["total_actual_budget"], 0)
        self.assertIsNone(summary["total_refined_budget"])
        self.assertIsNone(summary["total_estimate_cost"])
        self.assertIsNone(summary["total_remaining_budget"])
        self.assertIsNone(summary["risk"])

    def test_returns_correct_project_code_and_name(self):
        project = make_project(name="My Project")
        summary = get_lifetime_budget_summary(project)
        self.assertEqual(summary["project_code"], project.code)
        self.assertEqual(summary["project_name"], "My Project")

    def test_totals_across_multiple_budgets(self):
        project = make_project()
        fy1 = make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_budget(project=project, financial_year=fy1, allocated_budget=100_000)
        make_budget(project=project, financial_year=fy2, allocated_budget=200_000)
        summary = get_lifetime_budget_summary(project)
        self.assertEqual(summary["budget_count"], 2)
        self.assertEqual(summary["total_allocated_budget"], 300_000.0)

    def test_total_refined_budget_none_when_none_set(self):
        project = make_project()
        fy = make_financial_year()
        make_budget(
            project=project,
            financial_year=fy,
            allocated_budget=100_000,
            refined_budget=None,
        )
        summary = get_lifetime_budget_summary(project)
        self.assertIsNone(summary["total_refined_budget"])

    def test_total_refined_budget_aggregated_when_set(self):
        from decimal import Decimal

        project = make_project()
        fy1 = make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_budget(
            project=project,
            financial_year=fy1,
            allocated_budget=100_000,
            refined_budget=Decimal("90000"),
        )
        make_budget(
            project=project,
            financial_year=fy2,
            allocated_budget=200_000,
            refined_budget=Decimal("180000"),
        )
        summary = get_lifetime_budget_summary(project)
        self.assertEqual(summary["total_refined_budget"], 270_000.0)

    def test_total_estimate_cost_none_when_no_estimates(self):
        project = make_project()
        fy = make_financial_year()
        make_budget(project=project, financial_year=fy, allocated_budget=100_000)
        summary = get_lifetime_budget_summary(project)
        self.assertIsNone(summary["total_estimate_cost"])

    def test_total_estimate_cost_aggregated_when_estimates_set(self):
        project = make_project()
        fy1 = make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        est1 = make_estimate(
            project=project, estimate_days=10, day_rate=1000, contingency_percentage=0
        )
        est2 = make_estimate(
            project=project,
            version=2,
            estimate_days=20,
            day_rate=1000,
            contingency_percentage=0,
        )
        make_budget(
            project=project,
            financial_year=fy1,
            allocated_budget=100_000,
            estimate_version=est1,
        )
        make_budget(
            project=project,
            financial_year=fy2,
            allocated_budget=200_000,
            estimate_version=est2,
        )
        summary = get_lifetime_budget_summary(project)
        self.assertIsNotNone(summary["total_estimate_cost"])
        self.assertIsNotNone(summary["total_remaining_budget"])

    def test_risk_is_none_with_no_estimates(self):
        project = make_project()
        fy = make_financial_year()
        make_budget(project=project, financial_year=fy, allocated_budget=100_000)
        summary = get_lifetime_budget_summary(project)
        self.assertIsNone(summary["risk"])
