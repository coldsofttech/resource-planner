"""Integration tests for SprintDataImportForecastService DB-backed workflows."""

from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.core.exceptions import NotFoundException, ValidationException
from apps.sprints.constants import SprintDataImportStatus, SprintDataImportType
from apps.sprints.models import (
    SprintDataImport,
    SprintDataImportConfirmed,
    SprintDataImportRow,
)
from apps.sprints.selectors.sprint_data_import import get_has_review_for_import
from apps.sprints.services.sprint_data_import import SprintDataImportForecastService
from apps.sprints.tests.factories import FakeCsvFile, make_sprint
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user

CSV_HEADER = "Story Type,Jira ID,Title,Assignee,Efforts,Sprint,Label,Mapping\n"
CSV_ROW = (
    "Story,JIRA-1,Test Title,user@example.com,3600,Sprint 1,sample-label,PROJECT\n"
)


def _svc(user=None):
    if user is None:
        user = make_user()
    return SprintDataImportForecastService(user=user)


def _valid_csv(rows: int = 1) -> FakeCsvFile:
    content = CSV_HEADER + (CSV_ROW * rows)
    return FakeCsvFile(content, name="forecast.csv")


# ── upload() ──────────────────────────────────────────────────────────────────


class ForecastServiceUploadTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.user = make_user()
        self.sprint = make_sprint()
        self.team = make_team()
        self.svc = _svc(self.user)

    def test_upload_creates_sprint_data_import(self):
        self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.assertTrue(
            SprintDataImport.objects.filter(
                sprint=self.sprint,
                team=self.team,
                import_type=SprintDataImportType.FORECAST,
            ).exists()
        )

    def test_upload_creates_rows_from_csv(self):
        result = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(rows=2),
        )
        rows = SprintDataImportRow.objects.filter(import_record=result)
        self.assertEqual(rows.count(), 2)

    def test_upload_sets_version_number_to_one_for_first_upload(self):
        result = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.assertEqual(result.version_number, 1)

    def test_upload_increments_version_number_on_subsequent_upload(self):
        self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        result = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.assertEqual(result.version_number, 2)

    def test_upload_supersedes_previous_active_import(self):
        self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        superseded = SprintDataImport.objects.filter(
            sprint=self.sprint,
            team=self.team,
            import_type=SprintDataImportType.FORECAST,
            status=SprintDataImportStatus.SUPERSEDED,
        )
        self.assertEqual(superseded.count(), 1)

    def test_upload_new_import_has_active_status(self):
        result = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.assertEqual(result.status, SprintDataImportStatus.ACTIVE)

    def test_upload_sets_import_type_to_forecast(self):
        result = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.assertEqual(result.import_type, SprintDataImportType.FORECAST)

    def test_upload_raises_not_found_for_unknown_sprint(self):
        with self.assertRaises(NotFoundException):
            self.svc.upload(
                sprint_code="SPRINT-9999",
                team_code=self.team.code,
                file=_valid_csv(),
            )

    def test_upload_raises_not_found_for_unknown_team(self):
        with self.assertRaises(NotFoundException):
            self.svc.upload(
                sprint_code=self.sprint.code,
                team_code="TEAM-9999",
                file=_valid_csv(),
            )

    def test_upload_raises_validation_for_non_csv_file(self):
        bad_file = FakeCsvFile("data", name="data.xlsx")
        with self.assertRaises(ValidationException):
            self.svc.upload(
                sprint_code=self.sprint.code,
                team_code=self.team.code,
                file=bad_file,
            )

    def test_upload_raises_validation_for_missing_columns(self):
        bad_file = FakeCsvFile("Title,Assignee\nTest,user@x.com\n", name="bad.csv")
        with self.assertRaises(ValidationException):
            self.svc.upload(
                sprint_code=self.sprint.code,
                team_code=self.team.code,
                file=bad_file,
            )

    def test_upload_sets_file_name_on_import(self):
        result = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.assertEqual(result.file_name, "forecast.csv")

    def test_upload_sets_created_by(self):
        result = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.assertEqual(result.created_by, self.user)


# ── create_row() ──────────────────────────────────────────────────────────────


class ForecastServiceCreateRowTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.user = make_user()
        self.sprint = make_sprint()
        self.team = make_team()
        self.svc = _svc(self.user)
        self.import_record = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )

    def test_create_row_adds_row_to_import(self):
        self.svc.create_row(
            import_code=self.import_record.code,
            title="Manual Row",
        )
        self.assertEqual(
            SprintDataImportRow.objects.filter(
                import_record=self.import_record, is_manually_added=True
            ).count(),
            1,
        )

    def test_create_row_is_manually_added(self):
        row = self.svc.create_row(
            import_code=self.import_record.code,
            title="Manual Row",
        )
        self.assertTrue(row.is_manually_added)

    def test_create_row_raises_not_found_for_unknown_import(self):
        with self.assertRaises(NotFoundException):
            self.svc.create_row(
                import_code="SPTIMP-9999",
                title="X",
            )


# ── delete_row() ──────────────────────────────────────────────────────────────


class ForecastServiceDeleteRowTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.user = make_user()
        self.sprint = make_sprint()
        self.team = make_team()
        self.svc = _svc(self.user)
        self.import_record = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.manual_row = self.svc.create_row(
            import_code=self.import_record.code,
            title="To Delete",
        )
        self.csv_row = SprintDataImportRow.objects.filter(
            import_record=self.import_record, is_manually_added=False
        ).first()

    def test_delete_manually_added_row_removes_it_from_db(self):
        self.svc.delete_row(row_code=self.manual_row.code)
        self.assertFalse(
            SprintDataImportRow.objects.filter(pk=self.manual_row.pk).exists()
        )

    def test_delete_csv_row_soft_deletes(self):
        self.svc.delete_row(row_code=self.csv_row.code)
        self.csv_row.refresh_from_db()
        self.assertTrue(self.csv_row.is_deleted)

    def test_delete_unknown_row_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete_row(row_code="SPTIMPRW-9999")


# ── review() ──────────────────────────────────────────────────────────────────


class ForecastServiceReviewTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.user = make_user()
        self.sprint = make_sprint()
        self.team = make_team()
        self.svc = _svc(self.user)
        self.import_record = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )

    def test_review_returns_review_and_row_results(self):
        review, row_results = self.svc.review(import_code=self.import_record.code)
        self.assertTrue(review.code)
        self.assertIsInstance(row_results, dict)

    def test_review_creates_review_record(self):
        self.svc.review(import_code=self.import_record.code)
        self.assertTrue(get_has_review_for_import(self.import_record.pk))

    def test_review_raises_not_found_for_unknown_import(self):
        with self.assertRaises(NotFoundException):
            self.svc.review(import_code="SPTIMP-9999")


# ── confirm() ─────────────────────────────────────────────────────────────────


class ForecastServiceConfirmTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.user = make_user()
        self.sprint = make_sprint()
        self.team = make_team()
        self.svc = _svc(self.user)
        self.import_record = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )

    def test_confirm_without_review_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.svc.confirm(
                import_code=self.import_record.code,
                notes="",
            )

    def test_confirm_after_review_updates_status_to_confirmed(self):
        self.svc.review(import_code=self.import_record.code)
        self.svc.confirm(
            import_code=self.import_record.code,
            notes="override",
        )
        self.import_record.refresh_from_db()
        self.assertEqual(self.import_record.status, SprintDataImportStatus.CONFIRMED)

    def test_confirm_returns_review_complete_record(self):
        self.svc.review(import_code=self.import_record.code)
        result = self.svc.confirm(
            import_code=self.import_record.code,
            notes="override",
        )
        self.assertEqual(result.import_type, SprintDataImportType.FORECAST)
        self.assertIsNotNone(result.completed_at)
        self.assertTrue(result.override_applied)

    def test_confirm_creates_sprint_data_import_confirmed_records(self):
        self.svc.review(import_code=self.import_record.code)
        self.svc.confirm(
            import_code=self.import_record.code,
            notes="override",
        )
        self.assertTrue(
            SprintDataImportConfirmed.objects.filter(
                import_record=self.import_record
            ).exists()
        )

    def test_confirm_raises_not_found_for_unknown_import(self):
        with self.assertRaises(NotFoundException):
            self.svc.confirm(
                import_code="SPTIMP-9999",
                notes="",
            )

    def test_second_upload_and_confirm_supersedes_first_confirmed(self):
        self.svc.review(import_code=self.import_record.code)
        self.svc.confirm(import_code=self.import_record.code, notes="override")

        second = self.svc.upload(
            sprint_code=self.sprint.code,
            team_code=self.team.code,
            file=_valid_csv(),
        )
        self.svc.review(import_code=second.code)
        self.svc.confirm(import_code=second.code, notes="override")

        self.import_record.refresh_from_db()
        self.assertEqual(self.import_record.status, SprintDataImportStatus.SUPERSEDED)
