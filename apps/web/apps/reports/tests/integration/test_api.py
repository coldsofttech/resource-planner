from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.financial_years.tests.factories import make_financial_year
from apps.projects.constants import ProjectEstimateStatus
from apps.projects.models import ProjectStatus
from apps.projects.tests.factories import (
    make_estimate,
    make_programme,
    make_project,
    make_project_code,
    make_project_sprint_actual,
)
from apps.reports.tests.factories import make_kpi_estimate_accuracy_config
from apps.sprints.tests.factories import make_sprint
from apps.users.tests.factories import make_user

DATA_URL = "/api/v1/reports/standard/kpi-estimate-accuracy/data/"
EXPORT_SPECS_URL = "/api/v1/reports/standard/kpi-estimate-accuracy/export/specs/"
CONFIG_LIST_URL = "/api/v1/reports/standard/kpi-estimate-accuracy/configs/"
CONFIG_DETAIL_URL = "/api/v1/reports/standard/kpi-estimate-accuracy/configs/{}/"

MFR_DATA_URL = "/api/v1/reports/standard/monthly-finance-report/data/"
MFR_EXPORT_SPECS_URL = "/api/v1/reports/standard/monthly-finance-report/export/specs/"


class KPIEstimateAccuracyDataAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        self.sprint = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 14),
        )
        completed_status = ProjectStatus.objects.get(name="Completed")
        self.project = make_project(
            name="Migrate Billing",
            status=completed_status,
            sprint_completed_in=self.sprint,
        )
        make_estimate(
            project=self.project,
            version=1,
            status=ProjectEstimateStatus.APPROVED,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
        )
        make_project_sprint_actual(
            project=self.project, sprint=self.sprint, total_cost=9500
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DATA_URL, {"fy": self.fy.code, "month": "2025-04"})
        self.assertEqual(response.status_code, 401)

    def test_missing_query_params_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DATA_URL)
        self.assertEqual(response.status_code, 400)

    def test_unknown_fy_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DATA_URL, {"fy": "FY-999999", "month": "2025-04"})
        self.assertEqual(response.status_code, 404)

    def test_valid_request_returns_rows(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DATA_URL, {"fy": self.fy.code, "month": "2025-04"})
        self.assertEqual(response.status_code, 200)
        rows = response.data["data"]["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["project"], "Migrate Billing")

    def test_export_specs_returns_columns(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("columns", response.data["data"])


class KPIEstimateAccuracyConfigAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project(name="Migrate Billing")

    def test_unauthenticated_list_returns_401(self):
        response = self.client.get(CONFIG_LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_create_success(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "project_code": self.project.code,
            "month": "2025-04",
            "comment": "Scope changed mid-delivery.",
        }
        response = self.client.post(CONFIG_LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["month"], "2025-04")

    def test_create_duplicate_returns_409(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "project_code": self.project.code,
            "month": "2025-04",
            "comment": "First comment.",
        }
        self.client.post(CONFIG_LIST_URL, payload, format="json")
        response = self.client.post(CONFIG_LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, 409)

    def test_create_blank_comment_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "project_code": self.project.code,
            "month": "2025-04",
            "comment": "",
        }
        response = self.client.post(CONFIG_LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_list_filters_by_month(self):
        self.client.force_authenticate(user=self.user)
        make_kpi_estimate_accuracy_config(project=self.project, month="2025-04")
        make_kpi_estimate_accuracy_config(project=make_project(), month="2025-05")
        response = self.client.get(CONFIG_LIST_URL, {"month": "2025-04"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)

    def test_update_comment(self):
        self.client.force_authenticate(user=self.user)
        obj = make_kpi_estimate_accuracy_config(project=self.project)
        response = self.client.patch(
            CONFIG_DETAIL_URL.format(obj.code),
            {"comment": "Updated reasoning."},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["comment"], "Updated reasoning.")

    def test_delete_removes_config(self):
        self.client.force_authenticate(user=self.user)
        obj = make_kpi_estimate_accuracy_config(project=self.project)
        response = self.client.delete(CONFIG_DETAIL_URL.format(obj.code))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(CONFIG_DETAIL_URL.format(obj.code))
        self.assertEqual(response.status_code, 404)


class MonthlyFinanceReportDataAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        self.sprint = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 14),
        )
        self.programme = make_programme(name="Platform")
        self.project = make_project(name="Migrate Billing", programme=self.programme)
        self.project_code = make_project_code(project=self.project, value="FIN-001")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(
            MFR_DATA_URL, {"fy": self.fy.code, "month": "2025-04"}
        )
        self.assertEqual(response.status_code, 401)

    def test_missing_query_params_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MFR_DATA_URL)
        self.assertEqual(response.status_code, 400)

    def test_unknown_fy_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            MFR_DATA_URL, {"fy": "FY-999999", "month": "2025-04"}
        )
        self.assertEqual(response.status_code, 404)

    def test_sprint_without_actuals_returns_incomplete(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            MFR_DATA_URL, {"fy": self.fy.code, "month": "2025-04"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertFalse(data["is_complete"])
        self.assertEqual(len(data["sprints"]), 1)
        self.assertFalse(data["sprints"][0]["has_actuals"])
        self.assertEqual(data["rows"], [])

    def test_valid_request_returns_project_totals(self):
        make_project_sprint_actual(
            project=self.project,
            sprint=self.sprint,
            project_code=self.project_code,
            total_days=5,
            total_cost=5000,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            MFR_DATA_URL, {"fy": self.fy.code, "month": "2025-04"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertTrue(data["is_complete"])
        rows = data["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["project_code"], "FIN-001")
        self.assertEqual(rows[0]["project"], "Migrate Billing")
        self.assertEqual(data["totals"]["project_count"], 1)

    def test_export_specs_returns_columns(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MFR_EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("columns", response.data["data"])
