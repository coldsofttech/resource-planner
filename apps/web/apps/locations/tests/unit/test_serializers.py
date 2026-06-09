from django.test import SimpleTestCase

from apps.locations.serializers import (
    LocationCreateSerializer,
    LocationUpdateSerializer,
)


class LocationCreateSerializerTest(SimpleTestCase):
    def test_valid_payload_is_valid(self):
        s = LocationCreateSerializer(
            data={"city": "London", "country": "United Kingdom"}
        )
        self.assertTrue(s.is_valid())

    def test_missing_city_is_invalid(self):
        s = LocationCreateSerializer(data={"country": "United Kingdom"})
        self.assertFalse(s.is_valid())
        self.assertIn("city", s.errors)

    def test_missing_country_is_invalid(self):
        s = LocationCreateSerializer(data={"city": "London"})
        self.assertFalse(s.is_valid())
        self.assertIn("country", s.errors)

    def test_empty_payload_is_invalid(self):
        s = LocationCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("city", s.errors)
        self.assertIn("country", s.errors)

    def test_city_exceeding_max_length_is_invalid(self):
        s = LocationCreateSerializer(data={"city": "A" * 101, "country": "UK"})
        self.assertFalse(s.is_valid())
        self.assertIn("city", s.errors)

    def test_country_exceeding_max_length_is_invalid(self):
        s = LocationCreateSerializer(data={"city": "London", "country": "A" * 101})
        self.assertFalse(s.is_valid())
        self.assertIn("country", s.errors)

    def test_is_active_defaults_to_true(self):
        s = LocationCreateSerializer(data={"city": "London", "country": "UK"})
        s.is_valid()
        self.assertTrue(s.validated_data["is_active"])

    def test_is_default_defaults_to_false(self):
        s = LocationCreateSerializer(data={"city": "London", "country": "UK"})
        s.is_valid()
        self.assertFalse(s.validated_data["is_default"])

    def test_is_active_false_accepted(self):
        s = LocationCreateSerializer(
            data={"city": "London", "country": "UK", "is_active": False}
        )
        self.assertTrue(s.is_valid())
        self.assertFalse(s.validated_data["is_active"])

    def test_is_default_true_accepted(self):
        s = LocationCreateSerializer(
            data={"city": "London", "country": "UK", "is_default": True}
        )
        self.assertTrue(s.is_valid())
        self.assertTrue(s.validated_data["is_default"])


class LocationUpdateSerializerTest(SimpleTestCase):
    def test_empty_payload_is_valid(self):
        s = LocationUpdateSerializer(data={})
        self.assertTrue(s.is_valid())

    def test_city_only_is_valid(self):
        s = LocationUpdateSerializer(data={"city": "Manchester"})
        self.assertTrue(s.is_valid())

    def test_country_only_is_valid(self):
        s = LocationUpdateSerializer(data={"country": "Ireland"})
        self.assertTrue(s.is_valid())

    def test_city_exceeding_max_length_is_invalid(self):
        s = LocationUpdateSerializer(data={"city": "A" * 101})
        self.assertFalse(s.is_valid())
        self.assertIn("city", s.errors)

    def test_is_default_boolean_accepted(self):
        s = LocationUpdateSerializer(data={"is_default": True})
        self.assertTrue(s.is_valid())
