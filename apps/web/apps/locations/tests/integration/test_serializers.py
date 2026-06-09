from django.test import TestCase

from apps.locations.serializers import LocationDetailSerializer, LocationListSerializer
from apps.locations.tests.factories import make_location


class LocationListSerializerTest(TestCase):
    def test_contains_expected_fields(self):
        loc = make_location("London", "United Kingdom")
        data = LocationListSerializer(loc).data
        for field in [
            "code",
            "city",
            "country",
            "is_active",
            "is_default",
            "created_at",
        ]:
            self.assertIn(field, data)

    def test_city_value_matches(self):
        loc = make_location("London", "United Kingdom")
        data = LocationListSerializer(loc).data
        self.assertEqual(data["city"], "London")

    def test_country_value_matches(self):
        loc = make_location("London", "United Kingdom")
        data = LocationListSerializer(loc).data
        self.assertEqual(data["country"], "United Kingdom")

    def test_is_active_reflects_model(self):
        loc = make_location(is_active=False)
        data = LocationListSerializer(loc).data
        self.assertFalse(data["is_active"])

    def test_is_default_reflects_model(self):
        loc = make_location(is_default=True)
        data = LocationListSerializer(loc).data
        self.assertTrue(data["is_default"])


class LocationDetailSerializerTest(TestCase):
    def test_contains_expected_fields(self):
        loc = make_location("Dublin", "Ireland")
        data = LocationDetailSerializer(loc).data
        for field in [
            "code",
            "city",
            "country",
            "is_active",
            "is_default",
            "created_at",
            "updated_at",
        ]:
            self.assertIn(field, data)

    def test_city_value_matches(self):
        loc = make_location("Dublin", "Ireland")
        data = LocationDetailSerializer(loc).data
        self.assertEqual(data["city"], "Dublin")
