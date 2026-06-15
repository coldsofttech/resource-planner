from django.test import SimpleTestCase

from apps.holidays.services import HolidayImportService


def _make_import_service():
    return HolidayImportService(user=None)


class HolidayImportServiceValidateRowTest(SimpleTestCase):
    def setUp(self):
        self.svc = _make_import_service()

    def _make_valid(self, **overrides):
        row = {"name": "Christmas Day", "date": "2025-12-25", "location_code": "LOC-1"}
        row.update(overrides)
        return row

    def test_valid_row_returns_no_errors(self):
        errors = self.svc.validate_row(self._make_valid(), row_num=2)
        self.assertEqual(errors, [])

    def test_missing_name_returns_error(self):
        errors = self.svc.validate_row(self._make_valid(name=""), row_num=2)
        fields = [e["field"] for e in errors]
        self.assertIn("name", fields)

    def test_name_too_long_returns_error(self):
        errors = self.svc.validate_row(self._make_valid(name="x" * 121), row_num=2)
        fields = [e["field"] for e in errors]
        self.assertIn("name", fields)

    def test_name_at_max_length_passes(self):
        errors = self.svc.validate_row(self._make_valid(name="x" * 120), row_num=2)
        self.assertEqual(errors, [])

    def test_missing_date_returns_error(self):
        errors = self.svc.validate_row(self._make_valid(date=""), row_num=2)
        fields = [e["field"] for e in errors]
        self.assertIn("date", fields)

    def test_invalid_date_format_returns_error(self):
        errors = self.svc.validate_row(self._make_valid(date="25-12-2025"), row_num=2)
        fields = [e["field"] for e in errors]
        self.assertIn("date", fields)

    def test_missing_location_code_returns_error(self):
        errors = self.svc.validate_row(self._make_valid(location_code=""), row_num=2)
        fields = [e["field"] for e in errors]
        self.assertIn("location_code", fields)

    def test_multiple_missing_fields_return_multiple_errors(self):
        errors = self.svc.validate_row(
            {"name": "", "date": "", "location_code": ""}, row_num=2
        )
        self.assertGreater(len(errors), 1)

    def test_error_contains_row_number(self):
        errors = self.svc.validate_row(self._make_valid(name=""), row_num=5)
        self.assertEqual(errors[0]["row"], 5)

    def test_error_contains_field_key(self):
        errors = self.svc.validate_row(self._make_valid(name=""), row_num=2)
        self.assertIn("field", errors[0])

    def test_error_contains_message(self):
        errors = self.svc.validate_row(self._make_valid(name=""), row_num=2)
        self.assertIn("message", errors[0])
