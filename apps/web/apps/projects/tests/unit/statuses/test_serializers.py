from django.test import SimpleTestCase

from apps.projects.serializers import (
    ProjectSubStatusCreateSerializer,
    ProjectSubStatusReorderSerializer,
    ProjectSubStatusUpdateSerializer,
)


class ProjectSubStatusCreateSerializerTest(SimpleTestCase):
    def test_valid_with_name_only(self):
        s = ProjectSubStatusCreateSerializer(data={"name": "Draft"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_without_name(self):
        s = ProjectSubStatusCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_too_long_invalid(self):
        s = ProjectSubStatusCreateSerializer(data={"name": "x" * 101})
        self.assertFalse(s.is_valid())

    def test_name_at_max_length_is_valid(self):
        s = ProjectSubStatusCreateSerializer(data={"name": "x" * 100})
        self.assertTrue(s.is_valid(), s.errors)

    def test_is_active_defaults_to_true(self):
        s = ProjectSubStatusCreateSerializer(data={"name": "Draft"})
        self.assertTrue(s.is_valid())
        self.assertTrue(s.validated_data["is_active"])

    def test_is_active_can_be_false(self):
        s = ProjectSubStatusCreateSerializer(data={"name": "Draft", "is_active": False})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertFalse(s.validated_data["is_active"])


class ProjectSubStatusUpdateSerializerTest(SimpleTestCase):
    def test_valid_with_no_fields(self):
        s = ProjectSubStatusUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_name_only(self):
        s = ProjectSubStatusUpdateSerializer(data={"name": "Review"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_too_long_invalid(self):
        s = ProjectSubStatusUpdateSerializer(data={"name": "x" * 101})
        self.assertFalse(s.is_valid())

    def test_valid_with_is_active_only(self):
        s = ProjectSubStatusUpdateSerializer(data={"is_active": False})
        self.assertTrue(s.is_valid(), s.errors)


class ProjectSubStatusReorderSerializerTest(SimpleTestCase):
    def test_valid_with_codes_list(self):
        s = ProjectSubStatusReorderSerializer(
            data={"codes": ["PROJSUBSTAT-1", "PROJSUBSTAT-2"]}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_without_codes(self):
        s = ProjectSubStatusReorderSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("codes", s.errors)

    def test_invalid_with_empty_codes_list(self):
        s = ProjectSubStatusReorderSerializer(data={"codes": []})
        self.assertFalse(s.is_valid())

    def test_valid_with_single_code(self):
        s = ProjectSubStatusReorderSerializer(data={"codes": ["PROJSUBSTAT-1"]})
        self.assertTrue(s.is_valid(), s.errors)
