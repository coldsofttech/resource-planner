"""Unit tests for SprintDataImportForecastService pure logic (no DB)."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.core.exceptions import NotFoundException, ValidationException
from apps.sprints.constants import SprintDataImportType
from apps.sprints.services.sprint_data_import import SprintDataImportForecastService

# ── IMPORT_TYPE constant ───────────────────────────────────────────────────────


class ForecastServiceImportTypeTest(SimpleTestCase):
    def test_import_type_is_forecast(self):
        svc = SprintDataImportForecastService(user=MagicMock())
        self.assertEqual(svc.IMPORT_TYPE, SprintDataImportType.FORECAST)

    def test_template_filename_contains_forecast(self):
        svc = SprintDataImportForecastService(user=MagicMock())
        self.assertIn("forecast", svc.TEMPLATE_FILENAME)


# ── _validate_file ─────────────────────────────────────────────────────────────


class ForecastValidateFileTest(SimpleTestCase):
    def _svc(self):
        return SprintDataImportForecastService(user=MagicMock())

    def _fake_file(self, name: str = "data.csv", size_bytes: int = 100):
        f = MagicMock()
        f.name = name
        f.size = size_bytes
        return f

    def test_valid_csv_file_passes(self):
        svc = self._svc()
        svc._validate_file(self._fake_file("forecast.csv"))

    def test_non_csv_extension_raises_validation_error(self):
        svc = self._svc()
        with self.assertRaises(ValidationException):
            svc._validate_file(self._fake_file("data.xlsx"))

    def test_file_exceeding_size_limit_raises_validation_error(self):
        svc = self._svc()
        big_size = (svc.MAX_FILE_SIZE_MB + 1) * 1024 * 1024
        with self.assertRaises(ValidationException):
            svc._validate_file(self._fake_file(size_bytes=big_size))

    def test_file_at_exact_size_limit_passes(self):
        svc = self._svc()
        exact_size = svc.MAX_FILE_SIZE_MB * 1024 * 1024
        svc._validate_file(self._fake_file(size_bytes=exact_size))


# ── _validate_columns ──────────────────────────────────────────────────────────


class ForecastValidateColumnsTest(SimpleTestCase):
    def _svc(self):
        return SprintDataImportForecastService(user=MagicMock())

    def test_all_required_columns_passes(self):
        svc = self._svc()
        svc._validate_columns(svc.REQUIRED_COLUMNS)

    def test_missing_one_column_raises_validation_error(self):
        svc = self._svc()
        cols = [c for c in svc.REQUIRED_COLUMNS if c != "Assignee"]
        with self.assertRaises(ValidationException):
            svc._validate_columns(cols)

    def test_empty_fieldnames_raises_validation_error(self):
        svc = self._svc()
        with self.assertRaises(ValidationException):
            svc._validate_columns([])

    def test_none_fieldnames_raises_validation_error(self):
        svc = self._svc()
        with self.assertRaises(ValidationException):
            svc._validate_columns(None)

    def test_extra_columns_are_allowed(self):
        svc = self._svc()
        cols = svc.REQUIRED_COLUMNS + ["Extra Column"]
        svc._validate_columns(cols)


# ── _get_sprint raises NotFoundException ──────────────────────────────────────


class ForecastGetSprintTest(SimpleTestCase):
    @patch(
        "apps.sprints.services.sprint_data_import.get_sprint_by_code", return_value=None
    )
    def test_raises_not_found_when_sprint_missing(self, _mock):
        svc = SprintDataImportForecastService(user=MagicMock())
        with self.assertRaises(NotFoundException):
            svc._get_sprint("SPRINT-9999")

    @patch(
        "apps.sprints.services.sprint_data_import.get_sprint_by_code",
        side_effect=lambda code: MagicMock(pk=1, code=code),
    )
    def test_returns_sprint_when_found(self, _mock):
        svc = SprintDataImportForecastService(user=MagicMock())
        result = svc._get_sprint("SPRINT-1")
        self.assertEqual(result.code, "SPRINT-1")
