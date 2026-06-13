from django.test import TestCase

from apps.holidays.serializers import HolidayDetailSerializer, HolidayListSerializer
from apps.holidays.tests.factories import make_holiday


class HolidayListSerializerOutputTest(TestCase):
    def setUp(self):
        self.holiday = make_holiday()

    def test_has_required_fields(self):
        data = HolidayListSerializer(self.holiday).data
        for field in ["code", "name", "date", "location", "created_at"]:
            self.assertIn(field, data)

    def test_location_is_nested_object(self):
        data = HolidayListSerializer(self.holiday).data
        location = data["location"]
        self.assertIn("code", location)
        self.assertIn("city", location)
        self.assertIn("country", location)

    def test_code_matches_holiday(self):
        data = HolidayListSerializer(self.holiday).data
        self.assertEqual(data["code"], self.holiday.code)

    def test_date_serialized_as_string(self):
        data = HolidayListSerializer(self.holiday).data
        self.assertIsInstance(data["date"], str)

    def test_name_matches_holiday(self):
        data = HolidayListSerializer(self.holiday).data
        self.assertEqual(data["name"], self.holiday.name)


class HolidayDetailSerializerOutputTest(TestCase):
    def setUp(self):
        self.holiday = make_holiday()

    def test_has_required_fields(self):
        data = HolidayDetailSerializer(self.holiday).data
        for field in ["code", "name", "date", "location", "created_at", "updated_at"]:
            self.assertIn(field, data)

    def test_code_matches_holiday(self):
        data = HolidayDetailSerializer(self.holiday).data
        self.assertEqual(data["code"], self.holiday.code)

    def test_location_nested_has_city(self):
        data = HolidayDetailSerializer(self.holiday).data
        self.assertIn("city", data["location"])
