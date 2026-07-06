from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.constants import ProjectEstimateStatus
from apps.projects.models import ProjectActuals
from apps.projects.models.project_sprint_actual import ProjectSprintActual
from apps.projects.tests.factories import (
    make_estimate,
    make_financial_year,
    make_project,
)
from apps.sprints.constants import SprintStatus
from apps.sprints.tests.factories import make_sprint
from apps.users.tests.factories import make_user

ACTUALS_LIST_URL = "/api/v1/projects/{}/actuals/"
ACTUALS_SUMMARY_URL = "/api/v1/projects/{}/actuals/summary/"


# ------------------------------------------------------------------ #
# GET /api/v1/projects/<code>/actuals/                                 #
# ------------------------------------------------------------------ #


class ProjectActualsListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.project = make_project()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(ACTUALS_LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_response_contains_results_key(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_LIST_URL.format(self.project.code))
        self.assertIn("results", response.data["data"])

    def test_returns_empty_list_when_no_actuals(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_LIST_URL.format(self.project.code))
        self.assertEqual(response.data["data"]["results"], [])

    def test_returns_one_row_per_fy(self):
        fy1 = make_financial_year()
        fy2 = make_financial_year(
            start_date=(fy1.start_date.replace(year=fy1.start_date.year + 1)),
            end_date=(fy1.end_date.replace(year=fy1.end_date.year + 1)),
        )
        ProjectActuals.objects.create(
            project=self.project,
            fy=fy1,
            total_cost_to_date=Decimal("5000"),
            prev_fy_actuals=Decimal("0"),
        )
        ProjectActuals.objects.create(
            project=self.project,
            fy=fy2,
            total_cost_to_date=Decimal("3000"),
            prev_fy_actuals=Decimal("5000"),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_LIST_URL.format(self.project.code))
        self.assertEqual(len(response.data["data"]["results"]), 2)

    def test_fy_row_contains_expected_fields(self):
        fy = make_financial_year()
        ProjectActuals.objects.create(
            project=self.project,
            fy=fy,
            total_cost_to_date=Decimal("8000"),
            prev_fy_actuals=Decimal("0"),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_LIST_URL.format(self.project.code))
        row = response.data["data"]["results"][0]
        for key in ("fy", "fy_code", "total_days", "total_cost", "cumulative_cost"):
            self.assertIn(key, row)

    def test_sprint_drill_down_with_fy_param(self):
        fy = make_financial_year()
        sprint = make_sprint(financial_year=fy, status=SprintStatus.COMPLETED)
        ProjectSprintActual.objects.create(
            project=self.project,
            sprint=sprint,
            total_days=Decimal("3"),
            total_cost=Decimal("3000"),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            ACTUALS_LIST_URL.format(self.project.code), {"fy": fy.code}
        )
        self.assertEqual(response.status_code, 200)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertIn("sprint", results[0])

    def test_returns_404_for_unknown_project_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_LIST_URL.format("PROJ-NONE"))
        self.assertEqual(response.status_code, 404)


# ------------------------------------------------------------------ #
# GET /api/v1/projects/<code>/actuals/summary/                         #
# ------------------------------------------------------------------ #


class ProjectActualsSummaryAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.project = make_project()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(ACTUALS_SUMMARY_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_SUMMARY_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_response_contains_summary_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_SUMMARY_URL.format(self.project.code))
        data = response.data["data"]
        for key in (
            "estimate_cost",
            "estimate_cost_with_contingency",
            "total_actuals",
            "remaining_amount",
            "risk",
        ):
            self.assertIn(key, data)

    def test_estimate_cost_reflects_approved_estimate(self):
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=0,
            status=ProjectEstimateStatus.APPROVED,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_SUMMARY_URL.format(self.project.code))
        self.assertAlmostEqual(response.data["data"]["estimate_cost"], 10_000.0)

    def test_total_actuals_from_latest_fy(self):
        fy = make_financial_year()
        ProjectActuals.objects.create(
            project=self.project,
            fy=fy,
            total_cost_to_date=Decimal("7000"),
            prev_fy_actuals=Decimal("0"),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_SUMMARY_URL.format(self.project.code))
        self.assertAlmostEqual(response.data["data"]["total_actuals"], 7_000.0)

    def test_risk_is_none_when_no_estimate(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_SUMMARY_URL.format(self.project.code))
        self.assertIsNone(response.data["data"]["risk"])

    def test_risk_at_risk_when_actuals_exceed_contingency(self):
        make_estimate(
            project=self.project,
            estimate_days=10,
            day_rate=1000,
            contingency_percentage=10,
            status=ProjectEstimateStatus.APPROVED,
        )
        fy = make_financial_year()
        ProjectActuals.objects.create(
            project=self.project,
            fy=fy,
            total_cost_to_date=Decimal("12000"),
            prev_fy_actuals=Decimal("0"),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_SUMMARY_URL.format(self.project.code))
        self.assertEqual(response.data["data"]["risk"], "at_risk")

    def test_returns_404_for_unknown_project_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTUALS_SUMMARY_URL.format("PROJ-NONE"))
        self.assertEqual(response.status_code, 404)
