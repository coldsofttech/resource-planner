from django.test import SimpleTestCase

from apps.core.exceptions import ValidationException
from apps.employment_types.services import EmploymentTypeImportService
from apps.employment_types.tests.factories import make_csv_file


class EmploymentTypeImportValidateFileTest(SimpleTestCase):
    def setUp(self):
        self.svc = EmploymentTypeImportService(user=None)

    def test_accepts_csv_file(self):
        f = make_csv_file("name\nFull-time", "emp_types.csv")
        self.svc.validate_file(f)

    def test_rejects_unsupported_extension(self):
        f = make_csv_file("name\nFull-time", "emp_types.xlsx")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_rejects_txt_extension(self):
        f = make_csv_file("name\nFull-time", "emp_types.txt")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_rejects_file_exceeding_size_limit(self):
        f = make_csv_file("name\nFull-time", "emp_types.csv")
        f.size = (EmploymentTypeImportService.MAX_IMPORT_FILE_SIZE_MB + 1) * 1024 * 1024
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_accepts_file_at_exact_size_limit(self):
        f = make_csv_file("name\nFull-time", "emp_types.csv")
        f.size = EmploymentTypeImportService.MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024
        self.svc.validate_file(f)


class EmploymentTypeImportValidateRowTest(SimpleTestCase):
    def setUp(self):
        self.svc = EmploymentTypeImportService(user=None)

    def test_valid_row_returns_no_errors(self):
        errors = self.svc.validate_row({"name": "Full-time"}, row_num=2)
        self.assertEqual(errors, [])

    def test_missing_name_returns_error(self):
        errors = self.svc.validate_row({"name": ""}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "name")

    def test_name_exceeding_max_length_returns_error(self):
        errors = self.svc.validate_row({"name": "A" * 101}, row_num=3)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "name")

    def test_name_at_max_length_is_valid(self):
        errors = self.svc.validate_row({"name": "A" * 100}, row_num=2)
        self.assertEqual(errors, [])

    def test_error_includes_row_number(self):
        errors = self.svc.validate_row({"name": ""}, row_num=5)
        self.assertEqual(errors[0]["row"], 5)

    def test_whitespace_only_name_is_invalid(self):
        errors = self.svc.validate_row({"name": "   "}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "name")

    def test_none_name_is_invalid(self):
        errors = self.svc.validate_row({"name": None}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "name")
