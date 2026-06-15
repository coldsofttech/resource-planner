from django.test import SimpleTestCase

from apps.business_units.services import BusinessUnitImportService
from apps.business_units.tests.factories import make_csv_file


class BusinessUnitImportValidateFileTest(SimpleTestCase):
    def setUp(self):
        self.svc = BusinessUnitImportService(user=None)

    def test_accepts_csv_file(self):
        f = make_csv_file("name,short_name\nFinance,FIN", "business_units.csv")
        self.svc.validate_file(f)

    def test_rejects_unsupported_extension(self):
        from apps.core.exceptions import ValidationException

        f = make_csv_file("name,short_name\nFinance,FIN", "business_units.xlsx")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_rejects_txt_extension(self):
        from apps.core.exceptions import ValidationException

        f = make_csv_file("name,short_name\nFinance,FIN", "business_units.txt")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_rejects_file_exceeding_size_limit(self):
        from apps.core.exceptions import ValidationException

        f = make_csv_file("name,short_name\nFinance,FIN", "business_units.csv")
        f.size = (BusinessUnitImportService.MAX_IMPORT_FILE_SIZE_MB + 1) * 1024 * 1024
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_accepts_file_at_exact_size_limit(self):
        f = make_csv_file("name,short_name\nFinance,FIN", "business_units.csv")
        f.size = BusinessUnitImportService.MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024
        self.svc.validate_file(f)


class BusinessUnitImportValidateRowTest(SimpleTestCase):
    def setUp(self):
        self.svc = BusinessUnitImportService(user=None)

    def test_valid_row_returns_no_errors(self):
        errors = self.svc.validate_row(
            {"name": "Finance", "short_name": "FIN"}, row_num=2
        )
        self.assertEqual(errors, [])

    def test_missing_name_returns_error(self):
        errors = self.svc.validate_row({"name": "", "short_name": "FIN"}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "name")

    def test_missing_short_name_returns_error(self):
        errors = self.svc.validate_row({"name": "Finance", "short_name": ""}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "short_name")

    def test_both_missing_returns_two_errors(self):
        errors = self.svc.validate_row({"name": "", "short_name": ""}, row_num=2)
        self.assertEqual(len(errors), 2)

    def test_name_exceeding_max_length_returns_error(self):
        errors = self.svc.validate_row(
            {"name": "A" * 256, "short_name": "FIN"}, row_num=3
        )
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "name")

    def test_short_name_exceeding_max_length_returns_error(self):
        errors = self.svc.validate_row(
            {"name": "Finance", "short_name": "A" * 11}, row_num=3
        )
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "short_name")

    def test_name_at_max_length_is_valid(self):
        errors = self.svc.validate_row(
            {"name": "A" * 255, "short_name": "FIN"}, row_num=2
        )
        self.assertEqual(errors, [])

    def test_short_name_at_max_length_is_valid(self):
        errors = self.svc.validate_row(
            {"name": "Finance", "short_name": "A" * 10}, row_num=2
        )
        self.assertEqual(errors, [])

    def test_error_includes_row_number(self):
        errors = self.svc.validate_row({"name": "", "short_name": "FIN"}, row_num=5)
        self.assertEqual(errors[0]["row"], 5)

    def test_whitespace_only_name_is_invalid(self):
        errors = self.svc.validate_row({"name": "   ", "short_name": "FIN"}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "name")

    def test_none_name_is_invalid(self):
        errors = self.svc.validate_row({"name": None, "short_name": "FIN"}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "name")

    def test_none_short_name_is_invalid(self):
        errors = self.svc.validate_row(
            {"name": "Finance", "short_name": None}, row_num=2
        )
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "short_name")
