from datetime import date

from django.test import SimpleTestCase

from apps.financial_years.serializers import (
    FinancialYearCreateSerializer,
    FinancialYearUpdateSerializer,
)


class FinancialYearCreateSerializerValidationTest(SimpleTestCase):
    def _valid(self, **kwargs):
        data = {
            "start_date": date(2024, 4, 1),
            "end_date": date(2025, 3, 31),
            **kwargs,
        }
        s = FinancialYearCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        return s.validated_data

    def test_valid_dates_pass(self):
        data = self._valid()
        self.assertEqual(data["start_date"], date(2024, 4, 1))
        self.assertEqual(data["end_date"], date(2025, 3, 31))

    def test_start_date_required(self):
        s = FinancialYearCreateSerializer(data={"end_date": date(2025, 3, 31)})
        self.assertFalse(s.is_valid())
        self.assertIn("start_date", s.errors)

    def test_end_date_required(self):
        s = FinancialYearCreateSerializer(data={"start_date": date(2024, 4, 1)})
        self.assertFalse(s.is_valid())
        self.assertIn("end_date", s.errors)

    def test_end_date_must_be_after_start_date(self):
        s = FinancialYearCreateSerializer(
            data={"start_date": date(2025, 3, 31), "end_date": date(2024, 4, 1)}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("end_date", s.errors)

    def test_equal_dates_invalid(self):
        s = FinancialYearCreateSerializer(
            data={"start_date": date(2024, 4, 1), "end_date": date(2024, 4, 1)}
        )
        self.assertFalse(s.is_valid())

    def test_status_defaults_to_future(self):
        data = self._valid()
        self.assertEqual(data["status"], "future")

    def test_is_active_defaults_to_true(self):
        data = self._valid()
        self.assertTrue(data["is_active"])

    def test_note_defaults_to_empty(self):
        data = self._valid()
        self.assertEqual(data["note"], "")

    def test_invalid_status_rejected(self):
        s = FinancialYearCreateSerializer(
            data={
                "start_date": date(2024, 4, 1),
                "end_date": date(2025, 3, 31),
                "status": "unknown_status",
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("status", s.errors)


class FinancialYearUpdateSerializerValidationTest(SimpleTestCase):
    def test_all_fields_optional(self):
        s = FinancialYearUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_end_before_start_invalid(self):
        s = FinancialYearUpdateSerializer(
            data={"start_date": date(2025, 3, 31), "end_date": date(2024, 4, 1)}
        )
        self.assertFalse(s.is_valid())

    def test_valid_partial_update(self):
        s = FinancialYearUpdateSerializer(data={"status": "in_progress"}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
