from django.test import SimpleTestCase

from apps.holidays.serializers import HolidayCreateSerializer, HolidayUpdateSerializer


class HolidayCreateSerializerValidationTest(SimpleTestCase):
    def _make_valid(self, **overrides):
        data = {
            "name": "Christmas Day",
            "date": "2025-12-25",
            "location_code": "LOC-1",
        }
        data.update(overrides)
        return data

    def test_valid_payload_passes(self):
        s = HolidayCreateSerializer(data=self._make_valid())
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_required(self):
        data = self._make_valid()
        del data["name"]
        s = HolidayCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_date_required(self):
        data = self._make_valid()
        del data["date"]
        s = HolidayCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("date", s.errors)

    def test_location_code_required(self):
        data = self._make_valid()
        del data["location_code"]
        s = HolidayCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("location_code", s.errors)

    def test_name_exceeds_max_length_fails(self):
        s = HolidayCreateSerializer(data=self._make_valid(name="x" * 121))
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_at_max_length_passes(self):
        s = HolidayCreateSerializer(data=self._make_valid(name="x" * 120))
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_date_format_fails(self):
        s = HolidayCreateSerializer(data=self._make_valid(date="25-12-2025"))
        self.assertFalse(s.is_valid())
        self.assertIn("date", s.errors)


class HolidayUpdateSerializerValidationTest(SimpleTestCase):
    def test_all_fields_optional(self):
        s = HolidayUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_date_passes(self):
        s = HolidayUpdateSerializer(data={"date": "2025-06-15"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_date_format_fails(self):
        s = HolidayUpdateSerializer(data={"date": "not-a-date"})
        self.assertFalse(s.is_valid())
        self.assertIn("date", s.errors)

    def test_name_exceeds_max_length_fails(self):
        s = HolidayUpdateSerializer(data={"name": "x" * 121})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_at_max_length_passes(self):
        s = HolidayUpdateSerializer(data={"name": "x" * 120})
        self.assertTrue(s.is_valid(), s.errors)
