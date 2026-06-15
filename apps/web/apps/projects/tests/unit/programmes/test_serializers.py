from django.test import SimpleTestCase

from apps.projects.serializers import (
    ProgrammeCreateSerializer,
    ProgrammeUpdateSerializer,
)


class ProgrammeCreateSerializerTest(SimpleTestCase):
    def test_valid_with_name_only(self):
        s = ProgrammeCreateSerializer(data={"name": "Alpha"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_without_name(self):
        s = ProgrammeCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_too_long_invalid(self):
        s = ProgrammeCreateSerializer(data={"name": "x" * 256})
        self.assertFalse(s.is_valid())

    def test_description_optional(self):
        s = ProgrammeCreateSerializer(data={"name": "Alpha"})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data.get("description", ""), "")

    def test_is_active_defaults_to_true(self):
        s = ProgrammeCreateSerializer(data={"name": "Alpha"})
        self.assertTrue(s.is_valid())
        self.assertTrue(s.validated_data["is_active"])


class ProgrammeUpdateSerializerTest(SimpleTestCase):
    def test_valid_with_no_fields(self):
        s = ProgrammeUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_name_only(self):
        s = ProgrammeUpdateSerializer(data={"name": "New Name"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_too_long_invalid(self):
        s = ProgrammeUpdateSerializer(data={"name": "x" * 256})
        self.assertFalse(s.is_valid())

    def test_blank_description_allowed(self):
        s = ProgrammeUpdateSerializer(data={"description": ""})
        self.assertTrue(s.is_valid(), s.errors)
