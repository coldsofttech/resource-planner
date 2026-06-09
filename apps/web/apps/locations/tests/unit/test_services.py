from django.test import SimpleTestCase

from apps.core.exceptions import ValidationException
from apps.locations.services import LocationImportService
from apps.locations.tests.factories import make_csv_file


class LocationImportValidateFileTest(SimpleTestCase):
    def setUp(self):
        self.svc = LocationImportService(user=None)

    def test_accepts_csv_file(self):
        f = make_csv_file("city,country\nLondon,United Kingdom", "locations.csv")
        self.svc.validate_file(f)

    def test_rejects_unsupported_extension(self):
        f = make_csv_file("city,country\nLondon,UK", "locations.xlsx")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_rejects_txt_extension(self):
        f = make_csv_file("city,country\nLondon,UK", "locations.txt")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_rejects_file_exceeding_size_limit(self):
        f = make_csv_file("city,country\nLondon,UK", "locations.csv")
        f.size = (LocationImportService.MAX_IMPORT_FILE_SIZE_MB + 1) * 1024 * 1024
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_accepts_file_at_exact_size_limit(self):
        f = make_csv_file("city,country\nLondon,UK", "locations.csv")
        f.size = LocationImportService.MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024
        self.svc.validate_file(f)


class LocationImportValidateRowTest(SimpleTestCase):
    def setUp(self):
        self.svc = LocationImportService(user=None)

    def test_valid_row_returns_no_errors(self):
        errors = self.svc.validate_row({"city": "London", "country": "UK"}, row_num=2)
        self.assertEqual(errors, [])

    def test_missing_city_returns_error(self):
        errors = self.svc.validate_row({"city": "", "country": "UK"}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "city")

    def test_missing_country_returns_error(self):
        errors = self.svc.validate_row({"city": "London", "country": ""}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "country")

    def test_both_missing_returns_two_errors(self):
        errors = self.svc.validate_row({"city": "", "country": ""}, row_num=2)
        self.assertEqual(len(errors), 2)

    def test_city_exceeding_max_length_returns_error(self):
        errors = self.svc.validate_row({"city": "A" * 101, "country": "UK"}, row_num=3)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "city")

    def test_country_exceeding_max_length_returns_error(self):
        errors = self.svc.validate_row(
            {"city": "London", "country": "A" * 101}, row_num=3
        )
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "country")

    def test_city_at_max_length_is_valid(self):
        errors = self.svc.validate_row({"city": "A" * 100, "country": "UK"}, row_num=2)
        self.assertEqual(errors, [])

    def test_error_includes_row_number(self):
        errors = self.svc.validate_row({"city": "", "country": "UK"}, row_num=5)
        self.assertEqual(errors[0]["row"], 5)

    def test_whitespace_only_city_is_invalid(self):
        errors = self.svc.validate_row({"city": "   ", "country": "UK"}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "city")

    def test_none_city_is_invalid(self):
        errors = self.svc.validate_row({"city": None, "country": "UK"}, row_num=2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["field"], "city")
