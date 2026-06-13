from django.test import SimpleTestCase

from apps.projects.serializers import (
    ProjectTypeCreateSerializer,
    ProjectTypeUpdateSerializer,
)


class ProjectTypeCreateSerializerTest(SimpleTestCase):
    def test_valid_with_name_only(self):
        s = ProjectTypeCreateSerializer(data={"name": "Internal"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_without_name(self):
        s = ProjectTypeCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_too_long_invalid(self):
        s = ProjectTypeCreateSerializer(data={"name": "x" * 61})
        self.assertFalse(s.is_valid())

    def test_description_optional(self):
        s = ProjectTypeCreateSerializer(data={"name": "Internal"})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data.get("description", ""), "")

    def test_is_active_defaults_to_true(self):
        s = ProjectTypeCreateSerializer(data={"name": "Internal"})
        self.assertTrue(s.is_valid())
        self.assertTrue(s.validated_data["is_active"])

    def test_is_active_can_be_false(self):
        s = ProjectTypeCreateSerializer(data={"name": "Internal", "is_active": False})
        self.assertTrue(s.is_valid())
        self.assertFalse(s.validated_data["is_active"])

    def test_description_accepted(self):
        s = ProjectTypeCreateSerializer(
            data={"name": "Internal", "description": "An internal type"}
        )
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data["description"], "An internal type")


class ProjectTypeUpdateSerializerTest(SimpleTestCase):
    def test_valid_with_no_fields(self):
        s = ProjectTypeUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_name_only(self):
        s = ProjectTypeUpdateSerializer(data={"name": "External"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_too_long_invalid(self):
        s = ProjectTypeUpdateSerializer(data={"name": "x" * 61})
        self.assertFalse(s.is_valid())

    def test_blank_description_allowed(self):
        s = ProjectTypeUpdateSerializer(data={"description": ""})
        self.assertTrue(s.is_valid(), s.errors)

    def test_is_active_accepted(self):
        s = ProjectTypeUpdateSerializer(data={"is_active": False})
        self.assertTrue(s.is_valid())
        self.assertFalse(s.validated_data["is_active"])
