from django.test import SimpleTestCase

from apps.core.exceptions import ValidationException
from apps.roles.services import RoleImportService


def _make_file(name: str, content: str = "role\nDeveloper\n", size_mb: float = 0.001):
    class FakeFile:
        def __init__(self, filename, text, mb):
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = int(mb * 1024 * 1024)

        def read(self):
            return self._data

    return FakeFile(name, content, size_mb)


# ── RoleImportService.validate_file ───────────────────────────────────────────


class ValidateFileFormatTest(SimpleTestCase):
    def setUp(self):
        self.service = RoleImportService()

    def test_csv_file_is_accepted(self):
        f = _make_file("roles.csv")
        self.service.validate_file(f)  # should not raise

    def test_csv_uppercase_extension_is_accepted(self):
        f = _make_file("roles.CSV")
        self.service.validate_file(f)  # should not raise

    def test_xlsx_file_is_rejected(self):
        f = _make_file("roles.xlsx")
        with self.assertRaises(ValidationException):
            self.service.validate_file(f)

    def test_txt_file_is_rejected(self):
        f = _make_file("roles.txt")
        with self.assertRaises(ValidationException):
            self.service.validate_file(f)

    def test_json_file_is_rejected(self):
        f = _make_file("roles.json")
        with self.assertRaises(ValidationException):
            self.service.validate_file(f)

    def test_no_extension_file_is_rejected(self):
        f = _make_file("roles")
        with self.assertRaises(ValidationException):
            self.service.validate_file(f)


class ValidateFileSizeTest(SimpleTestCase):
    def setUp(self):
        self.service = RoleImportService()

    def test_file_within_size_limit_is_accepted(self):
        f = _make_file("roles.csv", size_mb=1.0)
        self.service.validate_file(f)  # should not raise

    def test_file_at_exact_limit_is_accepted(self):
        f = _make_file("roles.csv", size_mb=5.0)
        self.service.validate_file(f)  # should not raise

    def test_file_exceeding_size_limit_is_rejected(self):
        f = _make_file("roles.csv", size_mb=5.01)
        with self.assertRaises(ValidationException):
            self.service.validate_file(f)

    def test_very_large_file_is_rejected(self):
        f = _make_file("roles.csv", size_mb=100.0)
        with self.assertRaises(ValidationException):
            self.service.validate_file(f)


# ── RoleImportService.validate_row ────────────────────────────────────────────


class ValidateRowValidTest(SimpleTestCase):
    def setUp(self):
        self.service = RoleImportService()

    def test_valid_row_returns_no_errors(self):
        errors = self.service.validate_row({"role": "Developer"}, row_num=2)
        self.assertEqual(errors, [])

    def test_role_with_whitespace_returns_no_errors(self):
        errors = self.service.validate_row({"role": "  Developer  "}, row_num=2)
        self.assertEqual(errors, [])

    def test_role_at_max_length_returns_no_errors(self):
        errors = self.service.validate_row({"role": "A" * 100}, row_num=2)
        self.assertEqual(errors, [])


class ValidateRowMissingRoleTest(SimpleTestCase):
    def setUp(self):
        self.service = RoleImportService()

    def test_missing_role_key_returns_error(self):
        errors = self.service.validate_row({}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "role")
        self.assertEqual(errors[0]["row"], 2)

    def test_empty_role_returns_error(self):
        errors = self.service.validate_row({"role": ""}, row_num=3)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "role")

    def test_whitespace_only_role_returns_error(self):
        errors = self.service.validate_row({"role": "   "}, row_num=4)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "role")

    def test_none_role_returns_error(self):
        errors = self.service.validate_row({"role": None}, row_num=5)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "role")


class ValidateRowLengthTest(SimpleTestCase):
    def setUp(self):
        self.service = RoleImportService()

    def test_role_exceeding_100_chars_returns_error(self):
        errors = self.service.validate_row({"role": "A" * 101}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "role")
        self.assertEqual(errors[0]["row"], 2)

    def test_error_message_mentions_100_characters(self):
        errors = self.service.validate_row({"role": "A" * 101}, row_num=2)
        self.assertIn("100", errors[0]["message"])

    def test_row_number_is_preserved_in_error(self):
        errors = self.service.validate_row({"role": ""}, row_num=99)
        self.assertEqual(errors[0]["row"], 99)
