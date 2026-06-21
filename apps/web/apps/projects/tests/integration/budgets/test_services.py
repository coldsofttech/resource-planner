from datetime import date

from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.projects.models import ProjectBudget, ProjectBudgetStatusHistory
from apps.projects.services.budget import ProjectBudgetService
from apps.projects.tests.factories import (
    make_budget,
    make_estimate,
    make_financial_year,
    make_project,
)
from apps.users.tests.factories import make_user


def make_service(user=None):
    svc = ProjectBudgetService()
    svc.user = user or make_user()
    return svc


class ProjectBudgetServiceListTest(TestCase):
    def test_raises_not_found_for_unknown_project(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.list(project_code="PROJ-DOES-NOT-EXIST")

    def test_returns_paginated_result_for_valid_project(self):
        project = make_project()
        fy = make_financial_year()
        make_budget(project=project, financial_year=fy)
        svc = make_service()
        result = svc.list(project_code=project.code)
        self.assertEqual(result.pagination.total_count, 1)

    def test_returns_empty_list_when_no_budgets(self):
        project = make_project()
        svc = make_service()
        result = svc.list(project_code=project.code)
        self.assertEqual(result.pagination.total_count, 0)
        self.assertEqual(list(result.results), [])


class ProjectBudgetServiceCreateTest(TestCase):
    def test_creates_budget_successfully(self):
        project = make_project()
        fy = make_financial_year()
        svc = make_service()
        budget = svc.create(
            project_code=project.code,
            financial_year_code=fy.code,
            allocated_budget=100_000,
        )
        self.assertIsNotNone(budget.pk)
        self.assertEqual(budget.project.pk, project.pk)
        self.assertEqual(budget.financial_year.pk, fy.pk)

    def test_create_records_created_by(self):
        user = make_user()
        project = make_project()
        fy = make_financial_year()
        svc = make_service(user=user)
        budget = svc.create(
            project_code=project.code,
            financial_year_code=fy.code,
            allocated_budget=100_000,
        )
        self.assertEqual(budget.created_by.pk, user.pk)

    def test_create_records_history_entry(self):
        project = make_project()
        fy = make_financial_year()
        svc = make_service()
        budget = svc.create(
            project_code=project.code,
            financial_year_code=fy.code,
            allocated_budget=100_000,
        )
        count = ProjectBudgetStatusHistory.objects.filter(budget=budget).count()
        self.assertEqual(count, 1)

    def test_create_raises_not_found_for_unknown_project(self):
        fy = make_financial_year()
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.create(
                project_code="PROJ-NONE",
                financial_year_code=fy.code,
                allocated_budget=100_000,
            )

    def test_create_raises_not_found_for_unknown_financial_year(self):
        project = make_project()
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.create(
                project_code=project.code,
                financial_year_code="FY-NONE",
                allocated_budget=100_000,
            )

    def test_create_raises_already_exists_for_duplicate_project_and_fy(self):
        project = make_project()
        fy = make_financial_year()
        svc = make_service()
        svc.create(
            project_code=project.code,
            financial_year_code=fy.code,
            allocated_budget=100_000,
        )
        with self.assertRaises(AlreadyExistsException):
            svc.create(
                project_code=project.code,
                financial_year_code=fy.code,
                allocated_budget=200_000,
            )

    def test_create_with_refined_budget(self):
        project = make_project()
        fy = make_financial_year()
        svc = make_service()
        budget = svc.create(
            project_code=project.code,
            financial_year_code=fy.code,
            allocated_budget=100_000,
            refined_budget=90_000,
        )
        self.assertIsNotNone(budget.refined_budget)

    def test_create_with_note(self):
        project = make_project()
        fy = make_financial_year()
        svc = make_service()
        budget = svc.create(
            project_code=project.code,
            financial_year_code=fy.code,
            allocated_budget=100_000,
            note="Initial budget.",
        )
        self.assertEqual(budget.note, "Initial budget.")

    def test_create_with_estimate_version(self):
        project = make_project()
        fy = make_financial_year()
        estimate = make_estimate(project=project)
        svc = make_service()
        budget = svc.create(
            project_code=project.code,
            financial_year_code=fy.code,
            allocated_budget=100_000,
            estimate_version_code=estimate.code,
        )
        self.assertEqual(budget.estimate_version.pk, estimate.pk)

    def test_create_raises_not_found_for_unknown_estimate(self):
        project = make_project()
        fy = make_financial_year()
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.create(
                project_code=project.code,
                financial_year_code=fy.code,
                allocated_budget=100_000,
                estimate_version_code="PROJEST-NONE",
            )


class ProjectBudgetServiceUpdateTest(TestCase):
    def test_updates_allocated_budget(self):
        budget = make_budget(allocated_budget=100_000)
        svc = make_service()
        updated = svc.update(budget.code, allocated_budget=200_000)
        self.assertEqual(float(updated.allocated_budget), 200_000.0)

    def test_updates_refined_budget(self):
        budget = make_budget()
        svc = make_service()
        updated = svc.update(budget.code, refined_budget=80_000)
        self.assertIsNotNone(updated.refined_budget)
        self.assertEqual(float(updated.refined_budget), 80_000.0)

    def test_clears_refined_budget_when_set_to_none(self):
        from decimal import Decimal

        budget = make_budget(refined_budget=Decimal("80000"))
        svc = make_service()
        updated = svc.update(budget.code, refined_budget=None)
        self.assertIsNone(updated.refined_budget)

    def test_updates_note(self):
        budget = make_budget()
        svc = make_service()
        updated = svc.update(budget.code, note="Updated note.")
        self.assertEqual(updated.note, "Updated note.")

    def test_update_records_history_entry(self):
        budget = make_budget()
        initial_count = ProjectBudgetStatusHistory.objects.filter(budget=budget).count()
        svc = make_service()
        svc.update(budget.code, allocated_budget=200_000)
        new_count = ProjectBudgetStatusHistory.objects.filter(budget=budget).count()
        self.assertEqual(new_count, initial_count + 1)

    def test_update_raises_not_found_for_unknown_code(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.update("PROJBGT-NONE", allocated_budget=100_000)

    def test_update_records_updated_by(self):
        user = make_user(email="updater@example.com")
        budget = make_budget()
        svc = make_service(user=user)
        updated = svc.update(budget.code, note="Changed")
        self.assertEqual(updated.updated_by.pk, user.pk)

    def test_update_clears_estimate_version_when_code_is_empty(self):
        estimate = make_estimate()
        budget = make_budget(project=estimate.project, estimate_version=estimate)
        svc = make_service()
        updated = svc.update(budget.code, estimate_version_code="")
        self.assertIsNone(updated.estimate_version)


class ProjectBudgetServiceDeleteTest(TestCase):
    def test_deletes_budget(self):
        budget = make_budget()
        code = budget.code
        svc = make_service()
        svc.delete(code)
        self.assertFalse(ProjectBudget.objects.filter(code=code).exists())

    def test_delete_raises_not_found_for_unknown_code(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.delete("PROJBGT-NONE")


class ProjectBudgetServiceHistoryTest(TestCase):
    def test_returns_history_queryset(self):
        budget = make_budget()
        from apps.projects.tests.factories import make_budget_history

        make_budget_history(budget=budget)
        svc = make_service()
        qs = svc.history(budget.code)
        self.assertEqual(qs.count(), 1)

    def test_history_raises_not_found_for_unknown_budget(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.history("PROJBGT-NONE")


class ProjectBudgetServiceLifetimeTest(TestCase):
    def setUp(self):
        mark_setup_complete()

    def test_returns_lifetime_summary_dict(self):
        project = make_project()
        fy = make_financial_year()
        make_budget(project=project, financial_year=fy, allocated_budget=100_000)
        svc = make_service()
        summary = svc.lifetime(project.code)
        self.assertEqual(summary["project_code"], project.code)
        self.assertEqual(summary["budget_count"], 1)
        self.assertEqual(summary["total_allocated_budget"], 100_000.0)

    def test_lifetime_raises_not_found_for_unknown_project(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.lifetime("PROJ-NONE")

    def test_lifetime_returns_zero_totals_when_no_budgets(self):
        project = make_project()
        svc = make_service()
        summary = svc.lifetime(project.code)
        self.assertEqual(summary["budget_count"], 0)
        self.assertEqual(summary["total_allocated_budget"], 0)

    def test_lifetime_aggregates_multiple_budgets(self):
        project = make_project()
        fy1 = make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_budget(project=project, financial_year=fy1, allocated_budget=100_000)
        make_budget(project=project, financial_year=fy2, allocated_budget=200_000)
        svc = make_service()
        summary = svc.lifetime(project.code)
        self.assertEqual(summary["budget_count"], 2)
        self.assertEqual(summary["total_allocated_budget"], 300_000.0)
