from django.test import SimpleTestCase

from apps.teams.serializers import TeamCreateSerializer, TeamUpdateSerializer

# ── TeamCreateSerializer ──────────────────────────────────────────────────────


class TeamCreateSerializerValidationTest(SimpleTestCase):
    def test_valid_name_passes(self):
        s = TeamCreateSerializer(data={"name": "Alpha"})
        self.assertTrue(s.is_valid())

    def test_missing_name_fails(self):
        s = TeamCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_blank_name_fails(self):
        s = TeamCreateSerializer(data={"name": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_at_max_length_passes(self):
        s = TeamCreateSerializer(data={"name": "A" * 120})
        self.assertTrue(s.is_valid())

    def test_name_exceeding_max_length_fails(self):
        s = TeamCreateSerializer(data={"name": "A" * 121})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_description_optional(self):
        s = TeamCreateSerializer(data={"name": "Alpha"})
        self.assertTrue(s.is_valid())

    def test_description_defaults_to_empty_string(self):
        s = TeamCreateSerializer(data={"name": "Alpha"})
        s.is_valid()
        self.assertEqual(s.validated_data["description"], "")

    def test_description_blank_accepted(self):
        s = TeamCreateSerializer(data={"name": "Alpha", "description": ""})
        self.assertTrue(s.is_valid())

    def test_is_active_optional(self):
        s = TeamCreateSerializer(data={"name": "Alpha"})
        self.assertTrue(s.is_valid())

    def test_is_active_defaults_to_true(self):
        s = TeamCreateSerializer(data={"name": "Alpha"})
        s.is_valid()
        self.assertTrue(s.validated_data["is_active"])

    def test_is_active_false_accepted(self):
        s = TeamCreateSerializer(data={"name": "Alpha", "is_active": False})
        self.assertTrue(s.is_valid())
        self.assertFalse(s.validated_data["is_active"])


# ── TeamUpdateSerializer ──────────────────────────────────────────────────────


class TeamUpdateSerializerValidationTest(SimpleTestCase):
    def test_empty_payload_is_valid(self):
        s = TeamUpdateSerializer(data={})
        self.assertTrue(s.is_valid())

    def test_name_optional(self):
        s = TeamUpdateSerializer(data={"description": "Updated desc"})
        self.assertTrue(s.is_valid())

    def test_name_at_max_length_passes(self):
        s = TeamUpdateSerializer(data={"name": "A" * 120})
        self.assertTrue(s.is_valid())

    def test_name_exceeding_max_length_fails(self):
        s = TeamUpdateSerializer(data={"name": "A" * 121})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_description_blank_accepted(self):
        s = TeamUpdateSerializer(data={"description": ""})
        self.assertTrue(s.is_valid())

    def test_is_active_true_accepted(self):
        s = TeamUpdateSerializer(data={"is_active": True})
        self.assertTrue(s.is_valid())

    def test_is_active_false_accepted(self):
        s = TeamUpdateSerializer(data={"is_active": False})
        self.assertTrue(s.is_valid())

    def test_all_fields_together(self):
        s = TeamUpdateSerializer(
            data={"name": "Updated", "description": "New desc", "is_active": False}
        )
        self.assertTrue(s.is_valid())
