from django.test import SimpleTestCase

from apps.employment_types.serializers import (
    EmploymentTypeCreateSerializer,
    EmploymentTypeUpdateSerializer,
)

# ── EmploymentTypeCreateSerializer ────────────────────────────────────────────


class EmploymentTypeCreateSerializerValidationTest(SimpleTestCase):
    def test_valid_name_passes(self):
        s = EmploymentTypeCreateSerializer(data={"name": "Full-time"})
        self.assertTrue(s.is_valid())

    def test_missing_name_fails(self):
        s = EmploymentTypeCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_blank_name_fails(self):
        s = EmploymentTypeCreateSerializer(data={"name": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_at_max_length_passes(self):
        s = EmploymentTypeCreateSerializer(data={"name": "A" * 100})
        self.assertTrue(s.is_valid())

    def test_name_exceeding_max_length_fails(self):
        s = EmploymentTypeCreateSerializer(data={"name": "A" * 101})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_is_active_optional(self):
        s = EmploymentTypeCreateSerializer(data={"name": "Full-time"})
        self.assertTrue(s.is_valid())

    def test_is_active_defaults_to_true(self):
        s = EmploymentTypeCreateSerializer(data={"name": "Full-time"})
        s.is_valid()
        self.assertTrue(s.validated_data["is_active"])

    def test_is_active_false_accepted(self):
        s = EmploymentTypeCreateSerializer(
            data={"name": "Full-time", "is_active": False}
        )
        self.assertTrue(s.is_valid())
        self.assertFalse(s.validated_data["is_active"])

    def test_is_default_optional(self):
        s = EmploymentTypeCreateSerializer(data={"name": "Full-time"})
        self.assertTrue(s.is_valid())

    def test_is_default_defaults_to_false(self):
        s = EmploymentTypeCreateSerializer(data={"name": "Full-time"})
        s.is_valid()
        self.assertFalse(s.validated_data["is_default"])

    def test_is_default_true_accepted(self):
        s = EmploymentTypeCreateSerializer(
            data={"name": "Full-time", "is_default": True}
        )
        self.assertTrue(s.is_valid())
        self.assertTrue(s.validated_data["is_default"])


# ── EmploymentTypeUpdateSerializer ────────────────────────────────────────────


class EmploymentTypeUpdateSerializerValidationTest(SimpleTestCase):
    def test_empty_payload_is_valid(self):
        s = EmploymentTypeUpdateSerializer(data={})
        self.assertTrue(s.is_valid())

    def test_name_optional(self):
        s = EmploymentTypeUpdateSerializer(data={"is_active": True})
        self.assertTrue(s.is_valid())

    def test_name_at_max_length_passes(self):
        s = EmploymentTypeUpdateSerializer(data={"name": "A" * 100})
        self.assertTrue(s.is_valid())

    def test_name_exceeding_max_length_fails(self):
        s = EmploymentTypeUpdateSerializer(data={"name": "A" * 101})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_is_active_true_accepted(self):
        s = EmploymentTypeUpdateSerializer(data={"is_active": True})
        self.assertTrue(s.is_valid())

    def test_is_active_false_accepted(self):
        s = EmploymentTypeUpdateSerializer(data={"is_active": False})
        self.assertTrue(s.is_valid())

    def test_is_default_true_accepted(self):
        s = EmploymentTypeUpdateSerializer(data={"is_default": True})
        self.assertTrue(s.is_valid())

    def test_is_default_false_accepted(self):
        s = EmploymentTypeUpdateSerializer(data={"is_default": False})
        self.assertTrue(s.is_valid())

    def test_all_fields_together(self):
        s = EmploymentTypeUpdateSerializer(
            data={"name": "Part-time", "is_active": False, "is_default": True}
        )
        self.assertTrue(s.is_valid())
