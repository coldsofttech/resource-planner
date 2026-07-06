from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.financial_years.tests.factories import make_financial_year
from apps.projects.constants import ProjectEstimateStatus
from apps.projects.models import ProjectStatus
from apps.projects.tests.factories import (
    make_estimate,
    make_programme,
    make_project,
    make_project_code,
    make_project_collaborator,
    make_project_sprint_actual,
)
from apps.reports.services import (
    KPIEstimateAccuracyConfigService,
    KPIEstimateAccuracyReportService,
    MonthlyFinanceReportService,
)
from apps.reports.tests.factories import make_kpi_estimate_accuracy_config
from apps.sprints.tests.factories import make_sprint
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user


class KPIEstimateAccuracyConfigServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = KPIEstimateAccuracyConfigService(user=self.user)

    def test_create_success(self):
        project = make_project()
        obj = self.service.create(
            project_code=project.code, month="2025-04", comment="Delayed handover."
        )
        self.assertEqual(obj.project_id, project.id)
        self.assertEqual(obj.month, "2025-04")
        self.assertEqual(obj.created_by, self.user)

    def test_create_unknown_project_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.service.create(
                project_code="PROJ-999999", month="2025-04", comment="x"
            )

    def test_create_duplicate_raises_already_exists(self):
        project = make_project()
        self.service.create(project_code=project.code, month="2025-04", comment="x")
        with self.assertRaises(AlreadyExistsException):
            self.service.create(project_code=project.code, month="2025-04", comment="y")

    def test_create_same_project_different_month_allowed(self):
        project = make_project()
        self.service.create(project_code=project.code, month="2025-04", comment="x")
        obj2 = self.service.create(
            project_code=project.code, month="2025-05", comment="y"
        )
        self.assertIsNotNone(obj2.pk)


class KPIEstimateAccuracyConfigServiceUpdateDeleteTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = KPIEstimateAccuracyConfigService(user=self.user)

    def test_update_comment(self):
        obj = make_kpi_estimate_accuracy_config(comment="Old comment.")
        updated = self.service.update(code=obj.code, comment="New comment.")
        self.assertEqual(updated.comment, "New comment.")
        self.assertEqual(updated.updated_by, self.user)

    def test_get_unknown_code_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.service.get(code="KPICFG-999999")

    def test_delete_removes_record(self):
        obj = make_kpi_estimate_accuracy_config()
        self.service.delete(code=obj.code)
        with self.assertRaises(NotFoundException):
            self.service.get(code=obj.code)


class KPIEstimateAccuracyReportServiceGetDataTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        self.sprint = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 14),
        )
        self.completed_status = ProjectStatus.objects.get(name="Completed")
        self.programme = make_programme(name="Platform")
        self.team = make_team(name="Payments")
        self.project = make_project(
            name="Migrate Billing",
            status=self.completed_status,
            programme=self.programme,
            assigned_team=self.team,
            sprint_completed_in=self.sprint,
        )
        make_project_collaborator(self.project, make_team(name="Data"))
        self.estimate = make_estimate(
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
        self.service = KPIEstimateAccuracyReportService()

    def test_missing_fy_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.service.get_data(fy_code="", month="2025-04")

    def test_unknown_fy_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.service.get_data(fy_code="FY-999999", month="2025-04")

    def test_invalid_month_format_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.service.get_data(fy_code=self.fy.code, month="April-2025")

    def test_returns_completed_project_row(self):
        data = self.service.get_data(fy_code=self.fy.code, month="2025-04")
        self.assertEqual(len(data["rows"]), 1)
        row = data["rows"][0]
        self.assertEqual(row["project"], "Migrate Billing")
        self.assertEqual(row["programme"], "Platform")
        self.assertEqual(row["team"], "Payments")
        self.assertEqual(row["collaborators"], ["Data"])
        self.assertEqual(row["tshirt_size"], self.estimate.size)
        self.assertEqual(row["accuracy_pct"], 95.0)
        self.assertEqual(row["band_key"], "gt90")
        self.assertEqual(row["comment"], "")

    def test_month_with_no_completed_projects_returns_empty_rows(self):
        data = self.service.get_data(fy_code=self.fy.code, month="2025-05")
        self.assertEqual(data["rows"], [])

    def test_exception_comment_overrides_band(self):
        make_kpi_estimate_accuracy_config(
            project=self.project, month="2025-04", comment="Known scope change."
        )
        data = self.service.get_data(fy_code=self.fy.code, month="2025-04")
        row = data["rows"][0]
        self.assertEqual(row["band_key"], "exception")
        self.assertEqual(row["comment"], "Known scope change.")

    def test_chart_bands_grouped_by_size(self):
        data = self.service.get_data(fy_code=self.fy.code, month="2025-04")
        size = self.estimate.size
        if size in ("XS", "S"):
            self.assertIn("gt90", data["charts"]["xs_s"])
            self.assertEqual(data["charts"]["m_plus"], {})
        else:
            self.assertIn("gt90", data["charts"]["m_plus"])
            self.assertEqual(data["charts"]["xs_s"], {})


class MonthlyFinanceReportServiceGetDataTest(TestCase):
    def setUp(self):
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
        self.service = MonthlyFinanceReportService()

    def test_missing_fy_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.service.get_data(fy_code="", month="2025-04")

    def test_unknown_fy_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.service.get_data(fy_code="FY-999999", month="2025-04")

    def test_invalid_month_format_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.service.get_data(fy_code=self.fy.code, month="April-2025")

    def test_month_with_no_sprints_returns_incomplete_with_no_sprints(self):
        data = self.service.get_data(fy_code=self.fy.code, month="2025-05")
        self.assertEqual(data["sprints"], [])
        self.assertFalse(data["is_complete"])
        self.assertEqual(data["rows"], [])

    def test_sprint_without_actuals_is_incomplete(self):
        data = self.service.get_data(fy_code=self.fy.code, month="2025-04")
        self.assertEqual(len(data["sprints"]), 1)
        self.assertFalse(data["sprints"][0]["has_actuals"])
        self.assertFalse(data["is_complete"])
        self.assertEqual(data["rows"], [])

    def test_sprint_with_actuals_returns_project_totals(self):
        make_project_sprint_actual(
            project=self.project,
            sprint=self.sprint,
            project_code=self.project_code,
            total_days=5,
            total_cost=5000,
        )
        data = self.service.get_data(fy_code=self.fy.code, month="2025-04")
        self.assertTrue(data["sprints"][0]["has_actuals"])
        self.assertTrue(data["is_complete"])
        self.assertEqual(len(data["rows"]), 1)
        row = data["rows"][0]
        self.assertEqual(row["project_code"], "FIN-001")
        self.assertEqual(row["project"], "Migrate Billing")
        self.assertEqual(row["programme"], "Platform")
        self.assertEqual(Decimal(row["total_days"]), Decimal("5"))
        self.assertEqual(Decimal(row["total_cost"]), Decimal("5000"))
        self.assertEqual(data["totals"]["project_count"], 1)
        self.assertEqual(Decimal(data["totals"]["total_days"]), Decimal("5"))
        self.assertEqual(Decimal(data["totals"]["total_cost"]), Decimal("5000"))

    def test_multiple_sprints_in_month_aggregate_project_totals(self):
        sprint2 = make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            start_date=date(2025, 4, 15),
            end_date=date(2025, 4, 30),
        )
        make_project_sprint_actual(
            project=self.project,
            sprint=self.sprint,
            project_code=self.project_code,
            total_days=5,
            total_cost=5000,
        )
        make_project_sprint_actual(
            project=self.project,
            sprint=sprint2,
            project_code=self.project_code,
            total_days=3,
            total_cost=3000,
        )
        data = self.service.get_data(fy_code=self.fy.code, month="2025-04")
        self.assertEqual(len(data["sprints"]), 2)
        self.assertTrue(data["is_complete"])
        self.assertEqual(len(data["rows"]), 1)
        self.assertEqual(Decimal(data["rows"][0]["total_days"]), Decimal("8"))
        self.assertEqual(Decimal(data["rows"][0]["total_cost"]), Decimal("8000"))
