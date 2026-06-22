from django.test import SimpleTestCase

from apps.recharges.serializers import (
    ProjectTypeMappingCreateSerializer,
    ProjectTypeMappingUpdateSerializer,
    RechargeTypeCreateSerializer,
    RechargeTypeUpdateSerializer,
)

# ── RechargeTypeCreateSerializer ──────────────────────────────────────────────


class RechargeTypeCreateSerializerTest(SimpleTestCase):
    def _valid(self, data):
        s = RechargeTypeCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        return s.validated_data

    def _invalid(self, data):
        s = RechargeTypeCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        return s.errors

    def test_valid_upper_snake_case_name(self):
        data = self._valid({"name": "BAU"})
        self.assertEqual(data["name"], "BAU")

    def test_valid_name_with_underscore(self):
        data = self._valid({"name": "HOLIDAY_PROJECTS"})
        self.assertEqual(data["name"], "HOLIDAY_PROJECTS")

    def test_valid_name_with_digits(self):
        data = self._valid({"name": "PROJECT123"})
        self.assertEqual(data["name"], "PROJECT123")

    def test_description_defaults_to_empty(self):
        data = self._valid({"name": "BAU"})
        self.assertEqual(data["description"], "")

    def test_is_active_defaults_to_true(self):
        data = self._valid({"name": "BAU"})
        self.assertTrue(data["is_active"])

    def test_description_accepted(self):
        data = self._valid({"name": "BAU", "description": "Business as usual"})
        self.assertEqual(data["description"], "Business as usual")

    def test_is_active_false_accepted(self):
        data = self._valid({"name": "BAU", "is_active": False})
        self.assertFalse(data["is_active"])

    def test_missing_name_is_invalid(self):
        errors = self._invalid({})
        self.assertIn("name", errors)

    def test_lowercase_name_is_invalid(self):
        errors = self._invalid({"name": "bau"})
        self.assertIn("name", errors)

    def test_mixed_case_name_is_invalid(self):
        errors = self._invalid({"name": "Bau"})
        self.assertIn("name", errors)

    def test_name_with_spaces_is_invalid(self):
        errors = self._invalid({"name": "BAU TYPE"})
        self.assertIn("name", errors)

    def test_name_exceeding_50_chars_is_invalid(self):
        errors = self._invalid({"name": "A" * 51})
        self.assertIn("name", errors)

    def test_name_starting_with_digit_is_invalid(self):
        errors = self._invalid({"name": "1BAU"})
        self.assertIn("name", errors)


# ── RechargeTypeUpdateSerializer ──────────────────────────────────────────────


class RechargeTypeUpdateSerializerTest(SimpleTestCase):
    def _valid(self, data):
        s = RechargeTypeUpdateSerializer(data=data, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        return s.validated_data

    def _invalid(self, data):
        s = RechargeTypeUpdateSerializer(data=data, partial=True)
        self.assertFalse(s.is_valid())
        return s.errors

    def test_empty_payload_is_valid(self):
        data = self._valid({})
        self.assertNotIn("name", data)

    def test_valid_name_update(self):
        data = self._valid({"name": "PROJECT"})
        self.assertEqual(data["name"], "PROJECT")

    def test_description_update(self):
        data = self._valid({"description": "Updated description"})
        self.assertEqual(data["description"], "Updated description")

    def test_description_blank_accepted(self):
        data = self._valid({"description": ""})
        self.assertEqual(data["description"], "")

    def test_is_active_update(self):
        data = self._valid({"is_active": False})
        self.assertFalse(data["is_active"])

    def test_lowercase_name_is_invalid(self):
        errors = self._invalid({"name": "bau"})
        self.assertIn("name", errors)

    def test_name_exceeding_50_chars_is_invalid(self):
        errors = self._invalid({"name": "A" * 51})
        self.assertIn("name", errors)


# ── ProjectTypeMappingCreateSerializer ────────────────────────────────────────


class ProjectTypeMappingCreateSerializerTest(SimpleTestCase):
    def _valid(self, data):
        s = ProjectTypeMappingCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        return s.validated_data

    def _invalid(self, data):
        s = ProjectTypeMappingCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        return s.errors

    def test_valid_project_type_code(self):
        data = self._valid({"project_type_code": "PROJTYPE-1"})
        self.assertEqual(data["project_type_code"], "PROJTYPE-1")

    def test_missing_project_type_code_is_invalid(self):
        errors = self._invalid({})
        self.assertIn("project_type_code", errors)

    def test_empty_project_type_code_is_invalid(self):
        errors = self._invalid({"project_type_code": ""})
        self.assertIn("project_type_code", errors)


# ── ProjectTypeMappingUpdateSerializer ────────────────────────────────────────


class ProjectTypeMappingUpdateSerializerTest(SimpleTestCase):
    def _valid(self, data):
        s = ProjectTypeMappingUpdateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        return s.validated_data

    def _invalid(self, data):
        s = ProjectTypeMappingUpdateSerializer(data=data)
        self.assertFalse(s.is_valid())
        return s.errors

    def test_valid_project_type_code(self):
        data = self._valid({"project_type_code": "PROJTYPE-2"})
        self.assertEqual(data["project_type_code"], "PROJTYPE-2")

    def test_missing_project_type_code_is_invalid(self):
        errors = self._invalid({})
        self.assertIn("project_type_code", errors)

    def test_empty_project_type_code_is_invalid(self):
        errors = self._invalid({"project_type_code": ""})
        self.assertIn("project_type_code", errors)
