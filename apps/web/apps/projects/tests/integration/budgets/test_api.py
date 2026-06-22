from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectBudget
from apps.projects.tests.factories import (
    make_budget,
    make_financial_year,
    make_project,
)
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/projects/{}/budgets/"
DETAIL_URL = "/api/v1/projects/{}/budgets/{}/"
HISTORY_URL = "/api/v1/projects/{}/budgets/{}/history/"
LIFETIME_URL = "/api/v1/projects/{}/budgets/lifetime/"
EXPORT_SPECS_URL = "/api/v1/projects/{}/budgets/export/specs/"
EXPORT_URL = "/api/v1/projects/{}/budgets/export/"


class ProjectBudgetListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project()
        self.fy = make_financial_year()

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_authenticated_user(self):
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_empty_list_when_no_budgets(self):
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.data["data"]["pagination"]["total_count"], 0)
        self.assertEqual(response.data["data"]["results"], [])

    def test_returns_budget_in_list(self):
        make_budget(project=self.project, financial_year=self.fy)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.data["data"]["pagination"]["total_count"], 1)

    def test_list_response_contains_expected_fields(self):
        make_budget(project=self.project, financial_year=self.fy)
        response = self.client.get(LIST_URL.format(self.project.code))
        item = response.data["data"]["results"][0]
        self.assertIn("code", item)
        self.assertIn("financial_year", item)
        self.assertIn("allocated_budget", item)
        self.assertIn("actual_budget", item)
        self.assertIn("remaining_budget", item)

    def test_financial_year_name_is_populated(self):
        make_budget(project=self.project, financial_year=self.fy)
        response = self.client.get(LIST_URL.format(self.project.code))
        fy_data = response.data["data"]["results"][0]["financial_year"]
        self.assertIsNotNone(fy_data["name"])
        self.assertNotEqual(fy_data["name"], "")

    def test_returns_404_for_unknown_project(self):
        response = self.client.get(LIST_URL.format("PROJ-NONE"))
        self.assertEqual(response.status_code, 404)

    def test_only_returns_budgets_for_the_given_project(self):
        other_project = make_project(name="Other")
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        make_budget(project=self.project, financial_year=self.fy)
        make_budget(project=other_project, financial_year=fy2)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.data["data"]["pagination"]["total_count"], 1)


class ProjectBudgetCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project()
        self.fy = make_financial_year()

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"financial_year_code": self.fy.code, "allocated_budget": "100000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_creates_budget_and_returns_201(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"financial_year_code": self.fy.code, "allocated_budget": "100000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_created_budget_exists_in_db(self):
        self.client.post(
            LIST_URL.format(self.project.code),
            {"financial_year_code": self.fy.code, "allocated_budget": "100000.00"},
            format="json",
        )
        self.assertEqual(ProjectBudget.objects.filter(project=self.project).count(), 1)

    def test_missing_financial_year_code_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"allocated_budget": "100000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_allocated_budget_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"financial_year_code": self.fy.code},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_project_and_fy_returns_409(self):
        self.client.post(
            LIST_URL.format(self.project.code),
            {"financial_year_code": self.fy.code, "allocated_budget": "100000.00"},
            format="json",
        )
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"financial_year_code": self.fy.code, "allocated_budget": "200000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_unknown_project_returns_404(self):
        response = self.client.post(
            LIST_URL.format("PROJ-NONE"),
            {"financial_year_code": self.fy.code, "allocated_budget": "100000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_unknown_financial_year_returns_404(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"financial_year_code": "FY-NONE", "allocated_budget": "100000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_creates_with_optional_fields(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {
                "financial_year_code": self.fy.code,
                "allocated_budget": "100000.00",
                "refined_budget": "90000.00",
                "note": "Initial allocation.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)


class ProjectBudgetRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project()
        self.fy = make_financial_year()
        self.budget = make_budget(project=self.project, financial_year=self.fy)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(
            DETAIL_URL.format(self.project.code, self.budget.code)
        )
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_existing_budget(self):
        response = self.client.get(
            DETAIL_URL.format(self.project.code, self.budget.code)
        )
        self.assertEqual(response.status_code, 200)

    def test_returns_expected_fields(self):
        response = self.client.get(
            DETAIL_URL.format(self.project.code, self.budget.code)
        )
        data = response.data["data"]
        self.assertIn("code", data)
        self.assertIn("financial_year", data)
        self.assertIn("allocated_budget", data)
        self.assertIn("actual_budget", data)
        self.assertIn("remaining_budget", data)
        self.assertIn("note", data)

    def test_returns_404_for_unknown_budget(self):
        response = self.client.get(DETAIL_URL.format(self.project.code, "PROJBGT-NONE"))
        self.assertEqual(response.status_code, 404)


class ProjectBudgetUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project()
        self.fy = make_financial_year()
        self.budget = make_budget(project=self.project, financial_year=self.fy)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.budget.code),
            {"allocated_budget": "200000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_returns_200_on_successful_update(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.budget.code),
            {"allocated_budget": "200000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_update_persists_to_db(self):
        self.client.patch(
            DETAIL_URL.format(self.project.code, self.budget.code),
            {"allocated_budget": "200000.00"},
            format="json",
        )
        self.budget.refresh_from_db()
        self.assertEqual(float(self.budget.allocated_budget), 200_000.0)

    def test_returns_404_for_unknown_budget(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, "PROJBGT-NONE"),
            {"allocated_budget": "200000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_allocated_budget_returns_400(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.budget.code),
            {"allocated_budget": "not-a-number"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class ProjectBudgetDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project()
        self.fy = make_financial_year()
        self.budget = make_budget(project=self.project, financial_year=self.fy)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.budget.code)
        )
        self.assertEqual(response.status_code, 401)

    def test_returns_204_on_successful_delete(self):
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.budget.code)
        )
        self.assertEqual(response.status_code, 204)

    def test_budget_no_longer_exists_after_delete(self):
        code = self.budget.code
        self.client.delete(DETAIL_URL.format(self.project.code, code))
        self.assertFalse(ProjectBudget.objects.filter(code=code).exists())

    def test_returns_404_for_unknown_budget(self):
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, "PROJBGT-NONE")
        )
        self.assertEqual(response.status_code, 404)


class ProjectBudgetHistoryAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project()
        self.fy = make_financial_year()
        self.budget = make_budget(project=self.project, financial_year=self.fy)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(
            HISTORY_URL.format(self.project.code, self.budget.code)
        )
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_existing_budget(self):
        response = self.client.get(
            HISTORY_URL.format(self.project.code, self.budget.code)
        )
        self.assertEqual(response.status_code, 200)

    def test_history_contains_records(self):
        from apps.projects.tests.factories import make_budget_history

        make_budget_history(budget=self.budget)
        response = self.client.get(
            HISTORY_URL.format(self.project.code, self.budget.code)
        )
        self.assertGreater(len(response.data["data"]), 0)

    def test_returns_404_for_unknown_budget(self):
        response = self.client.get(
            HISTORY_URL.format(self.project.code, "PROJBGT-NONE")
        )
        self.assertEqual(response.status_code, 404)


class ProjectBudgetLifetimeAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project()
        self.fy = make_financial_year()

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(LIFETIME_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_authenticated_user(self):
        response = self.client.get(LIFETIME_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_lifetime_summary_fields(self):
        make_budget(project=self.project, financial_year=self.fy)
        response = self.client.get(LIFETIME_URL.format(self.project.code))
        data = response.data["data"]
        self.assertIn("project_code", data)
        self.assertIn("budget_count", data)
        self.assertIn("total_allocated_budget", data)
        self.assertIn("total_actual_budget", data)
        self.assertIn("total_remaining_budget", data)

    def test_budget_count_reflects_actual_count(self):
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        make_budget(project=self.project, financial_year=self.fy)
        make_budget(project=self.project, financial_year=fy2)
        response = self.client.get(LIFETIME_URL.format(self.project.code))
        self.assertEqual(response.data["data"]["budget_count"], 2)

    def test_returns_404_for_unknown_project(self):
        response = self.client.get(LIFETIME_URL.format("PROJ-NONE"))
        self.assertEqual(response.status_code, 404)


class ProjectBudgetExportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project()

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(EXPORT_SPECS_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_authenticated_user(self):
        response = self.client.get(EXPORT_SPECS_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_response_contains_columns_key(self):
        response = self.client.get(EXPORT_SPECS_URL.format(self.project.code))
        self.assertIn("columns", response.data["data"])


class ProjectBudgetExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project()
        self.fy = make_financial_year()
        make_budget(project=self.project, financial_year=self.fy)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(EXPORT_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_authenticated_user(self):
        response = self.client.get(EXPORT_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_csv_by_default(self):
        response = self.client.get(EXPORT_URL.format(self.project.code))
        self.assertIn("text/csv", response.get("Content-Type", ""))
