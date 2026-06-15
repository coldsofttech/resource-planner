from django.test import SimpleTestCase

from apps.business_units.serializers import (
    BusinessUnitCreateSerializer,
    BusinessUnitUpdateSerializer,
)

# ── BusinessUnitCreateSerializer ──────────────────────────────────────────────


class BusinessUnitCreateSerializerValidationTest(SimpleTestCase):
    def test_valid_payload_passes(self):
        s = BusinessUnitCreateSerializer(data={"name": "Finance", "short_name": "FIN"})
        self.assertTrue(s.is_valid())

    def test_missing_name_fails(self):
        s = BusinessUnitCreateSerializer(data={"short_name": "FIN"})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_blank_name_fails(self):
        s = BusinessUnitCreateSerializer(data={"name": "", "short_name": "FIN"})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_at_max_length_passes(self):
        s = BusinessUnitCreateSerializer(data={"name": "A" * 255, "short_name": "FIN"})
        self.assertTrue(s.is_valid())

    def test_name_exceeding_max_length_fails(self):
        s = BusinessUnitCreateSerializer(data={"name": "A" * 256, "short_name": "FIN"})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_missing_short_name_fails(self):
        s = BusinessUnitCreateSerializer(data={"name": "Finance"})
        self.assertFalse(s.is_valid())
        self.assertIn("short_name", s.errors)

    def test_blank_short_name_fails(self):
        s = BusinessUnitCreateSerializer(data={"name": "Finance", "short_name": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("short_name", s.errors)

    def test_short_name_at_max_length_passes(self):
        s = BusinessUnitCreateSerializer(
            data={"name": "Finance", "short_name": "A" * 10}
        )
        self.assertTrue(s.is_valid())

    def test_short_name_exceeding_max_length_fails(self):
        s = BusinessUnitCreateSerializer(
            data={"name": "Finance", "short_name": "A" * 11}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("short_name", s.errors)

    def test_is_active_optional(self):
        s = BusinessUnitCreateSerializer(data={"name": "Finance", "short_name": "FIN"})
        self.assertTrue(s.is_valid())

    def test_is_active_defaults_to_true(self):
        s = BusinessUnitCreateSerializer(data={"name": "Finance", "short_name": "FIN"})
        s.is_valid()
        self.assertTrue(s.validated_data["is_active"])

    def test_is_active_false_accepted(self):
        s = BusinessUnitCreateSerializer(
            data={"name": "Finance", "short_name": "FIN", "is_active": False}
        )
        self.assertTrue(s.is_valid())
        self.assertFalse(s.validated_data["is_active"])


# ── BusinessUnitUpdateSerializer ──────────────────────────────────────────────


class BusinessUnitUpdateSerializerValidationTest(SimpleTestCase):
    def test_empty_payload_is_valid(self):
        s = BusinessUnitUpdateSerializer(data={})
        self.assertTrue(s.is_valid())

    def test_name_optional(self):
        s = BusinessUnitUpdateSerializer(data={"short_name": "FIN"})
        self.assertTrue(s.is_valid())

    def test_name_at_max_length_passes(self):
        s = BusinessUnitUpdateSerializer(data={"name": "A" * 255})
        self.assertTrue(s.is_valid())

    def test_name_exceeding_max_length_fails(self):
        s = BusinessUnitUpdateSerializer(data={"name": "A" * 256})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_short_name_optional(self):
        s = BusinessUnitUpdateSerializer(data={"name": "Finance"})
        self.assertTrue(s.is_valid())

    def test_short_name_at_max_length_passes(self):
        s = BusinessUnitUpdateSerializer(data={"short_name": "A" * 10})
        self.assertTrue(s.is_valid())

    def test_short_name_exceeding_max_length_fails(self):
        s = BusinessUnitUpdateSerializer(data={"short_name": "A" * 11})
        self.assertFalse(s.is_valid())
        self.assertIn("short_name", s.errors)

    def test_is_active_true_accepted(self):
        s = BusinessUnitUpdateSerializer(data={"is_active": True})
        self.assertTrue(s.is_valid())

    def test_is_active_false_accepted(self):
        s = BusinessUnitUpdateSerializer(data={"is_active": False})
        self.assertTrue(s.is_valid())

    def test_all_fields_together(self):
        s = BusinessUnitUpdateSerializer(
            data={"name": "Technology", "short_name": "TECH", "is_active": False}
        )
        self.assertTrue(s.is_valid())
