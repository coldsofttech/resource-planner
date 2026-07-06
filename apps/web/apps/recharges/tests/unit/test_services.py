from django.test import SimpleTestCase

from apps.core.exceptions import ValidationException
from apps.recharges.services import (
    ProjectTypeMappingImportService,
    RechargeDetailService,
    RechargeTypeImportService,
)


class _FakeFile:
    """Minimal file-like object for validate_file() tests."""

    def __init__(self, name: str = "test.csv", size: int = 1024) -> None:
        self.name = name
        self.size = size


# ── RechargeTypeImportService.validate_row ───────────────────────────────────


class RechargeTypeImportValidateRowTest(SimpleTestCase):
    def setUp(self):
        self.svc = RechargeTypeImportService(user=None)

    def test_valid_name_returns_no_errors(self):
        errors = self.svc.validate_row({"name": "BAU"}, 2)
        self.assertEqual(errors, [])

    def test_valid_name_with_underscore_returns_no_errors(self):
        errors = self.svc.validate_row({"name": "BAU_TRAVEL"}, 2)
        self.assertEqual(errors, [])

    def test_valid_name_with_digits_returns_no_errors(self):
        errors = self.svc.validate_row({"name": "BAU2"}, 2)
        self.assertEqual(errors, [])

    def test_name_at_max_length_returns_no_errors(self):
        errors = self.svc.validate_row({"name": "A" * 50}, 2)
        self.assertEqual(errors, [])

    def test_empty_name_returns_error(self):
        errors = self.svc.validate_row({"name": ""}, 2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "name")

    def test_whitespace_only_name_returns_error(self):
        errors = self.svc.validate_row({"name": "   "}, 2)
        self.assertEqual(len(errors), 1)

    def test_none_name_returns_error(self):
        errors = self.svc.validate_row({"name": None}, 2)
        self.assertEqual(len(errors), 1)

    def test_missing_name_key_returns_error(self):
        errors = self.svc.validate_row({}, 2)
        self.assertEqual(len(errors), 1)

    def test_name_over_max_length_returns_error(self):
        errors = self.svc.validate_row({"name": "A" * 51}, 2)
        self.assertEqual(len(errors), 1)
        self.assertIn("50", errors[0]["message"])

    def test_lowercase_name_returns_error(self):
        errors = self.svc.validate_row({"name": "bau"}, 2)
        self.assertEqual(len(errors), 1)
        self.assertIn("UPPER_SNAKE_CASE", errors[0]["message"])

    def test_mixed_case_name_returns_error(self):
        errors = self.svc.validate_row({"name": "Bau"}, 2)
        self.assertEqual(len(errors), 1)

    def test_name_with_space_returns_error(self):
        errors = self.svc.validate_row({"name": "BAU TRAVEL"}, 2)
        self.assertEqual(len(errors), 1)

    def test_name_with_hyphen_returns_error(self):
        errors = self.svc.validate_row({"name": "BAU-TRAVEL"}, 2)
        self.assertEqual(len(errors), 1)

    def test_error_reports_correct_row_number(self):
        errors = self.svc.validate_row({"name": ""}, 7)
        self.assertEqual(errors[0]["row"], 7)

    def test_only_one_error_per_invalid_name(self):
        errors = self.svc.validate_row({"name": ""}, 2)
        self.assertEqual(len(errors), 1)


# ── RechargeTypeImportService.validate_file ──────────────────────────────────


class RechargeTypeImportValidateFileTest(SimpleTestCase):
    def setUp(self):
        self.svc = RechargeTypeImportService(user=None)

    def test_valid_csv_does_not_raise(self):
        self.svc.validate_file(_FakeFile("data.csv", size=1024))

    def test_xlsx_extension_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.svc.validate_file(_FakeFile("data.xlsx", size=1024))

    def test_txt_extension_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.svc.validate_file(_FakeFile("data.txt", size=1024))

    def test_no_extension_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.svc.validate_file(_FakeFile("data", size=1024))

    def test_file_exactly_at_size_limit_does_not_raise(self):
        max_bytes = 5 * 1024 * 1024
        self.svc.validate_file(_FakeFile("data.csv", size=max_bytes))

    def test_file_over_size_limit_raises_validation_error(self):
        over_limit = 5 * 1024 * 1024 + 1
        with self.assertRaises(ValidationException):
            self.svc.validate_file(_FakeFile("data.csv", size=over_limit))


# ── ProjectTypeMappingImportService.validate_row ─────────────────────────────


class ProjectTypeMappingImportValidateRowTest(SimpleTestCase):
    def setUp(self):
        self.svc = ProjectTypeMappingImportService(user=None, recharge_type_code="")

    def test_valid_code_returns_no_errors(self):
        errors = self.svc.validate_row({"project_type_code": "PRJTY-1"}, 2)
        self.assertEqual(errors, [])

    def test_empty_code_returns_error(self):
        errors = self.svc.validate_row({"project_type_code": ""}, 2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "project_type_code")

    def test_none_code_returns_error(self):
        errors = self.svc.validate_row({"project_type_code": None}, 2)
        self.assertEqual(len(errors), 1)

    def test_missing_key_returns_error(self):
        errors = self.svc.validate_row({}, 2)
        self.assertEqual(len(errors), 1)

    def test_error_reports_correct_row_number(self):
        errors = self.svc.validate_row({"project_type_code": ""}, 9)
        self.assertEqual(errors[0]["row"], 9)

    def test_whitespace_only_code_returns_error(self):
        errors = self.svc.validate_row({"project_type_code": "   "}, 2)
        self.assertEqual(len(errors), 1)


# ── ProjectTypeMappingImportService.validate_file ────────────────────────────


class ProjectTypeMappingImportValidateFileTest(SimpleTestCase):
    def setUp(self):
        self.svc = ProjectTypeMappingImportService(user=None, recharge_type_code="")

    def test_valid_csv_does_not_raise(self):
        self.svc.validate_file(_FakeFile("mappings.csv", size=1024))

    def test_xlsx_extension_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.svc.validate_file(_FakeFile("mappings.xlsx", size=1024))

    def test_json_extension_raises_validation_error(self):
        with self.assertRaises(ValidationException):
            self.svc.validate_file(_FakeFile("mappings.json", size=1024))

    def test_file_over_size_limit_raises_validation_error(self):
        over_limit = 5 * 1024 * 1024 + 1
        with self.assertRaises(ValidationException):
            self.svc.validate_file(_FakeFile("mappings.csv", size=over_limit))

    def test_file_at_size_limit_does_not_raise(self):
        max_bytes = 5 * 1024 * 1024
        self.svc.validate_file(_FakeFile("mappings.csv", size=max_bytes))


# ── RechargeDetailService initialisation ─────────────────────────────────────


class RechargeDetailServiceInitTest(SimpleTestCase):
    def test_user_stored_on_instance(self):
        sentinel = object()
        svc = RechargeDetailService(user=sentinel)
        self.assertIs(svc.user, sentinel)

    def test_user_none_is_accepted(self):
        svc = RechargeDetailService(user=None)
        self.assertIsNone(svc.user)
