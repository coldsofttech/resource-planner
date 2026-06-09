from django.test import SimpleTestCase

from apps.skills.serializers import SkillCreateSerializer, SkillUpdateSerializer

# ── SkillCreateSerializer ─────────────────────────────────────────────────────


class SkillCreateSerializerValidationTest(SimpleTestCase):
    def test_valid_skill_passes(self):
        s = SkillCreateSerializer(data={"skill": "Python"})
        self.assertTrue(s.is_valid())

    def test_missing_skill_fails(self):
        s = SkillCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("skill", s.errors)

    def test_blank_skill_fails(self):
        s = SkillCreateSerializer(data={"skill": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("skill", s.errors)

    def test_skill_at_max_length_passes(self):
        s = SkillCreateSerializer(data={"skill": "A" * 20})
        self.assertTrue(s.is_valid())

    def test_skill_exceeding_max_length_fails(self):
        s = SkillCreateSerializer(data={"skill": "A" * 21})
        self.assertFalse(s.is_valid())
        self.assertIn("skill", s.errors)

    def test_description_optional(self):
        s = SkillCreateSerializer(data={"skill": "Python"})
        self.assertTrue(s.is_valid())

    def test_description_defaults_to_empty_string(self):
        s = SkillCreateSerializer(data={"skill": "Python"})
        s.is_valid()
        self.assertEqual(s.validated_data["description"], "")

    def test_description_blank_accepted(self):
        s = SkillCreateSerializer(data={"skill": "Python", "description": ""})
        self.assertTrue(s.is_valid())

    def test_is_active_optional(self):
        s = SkillCreateSerializer(data={"skill": "Python"})
        self.assertTrue(s.is_valid())

    def test_is_active_defaults_to_true(self):
        s = SkillCreateSerializer(data={"skill": "Python"})
        s.is_valid()
        self.assertTrue(s.validated_data["is_active"])

    def test_is_active_false_accepted(self):
        s = SkillCreateSerializer(data={"skill": "Python", "is_active": False})
        self.assertTrue(s.is_valid())
        self.assertFalse(s.validated_data["is_active"])


# ── SkillUpdateSerializer ─────────────────────────────────────────────────────


class SkillUpdateSerializerValidationTest(SimpleTestCase):
    def test_empty_payload_is_valid(self):
        s = SkillUpdateSerializer(data={})
        self.assertTrue(s.is_valid())

    def test_skill_optional(self):
        s = SkillUpdateSerializer(data={"description": "Updated desc"})
        self.assertTrue(s.is_valid())

    def test_skill_at_max_length_passes(self):
        s = SkillUpdateSerializer(data={"skill": "A" * 20})
        self.assertTrue(s.is_valid())

    def test_skill_exceeding_max_length_fails(self):
        s = SkillUpdateSerializer(data={"skill": "A" * 21})
        self.assertFalse(s.is_valid())
        self.assertIn("skill", s.errors)

    def test_description_blank_accepted(self):
        s = SkillUpdateSerializer(data={"description": ""})
        self.assertTrue(s.is_valid())

    def test_is_active_true_accepted(self):
        s = SkillUpdateSerializer(data={"is_active": True})
        self.assertTrue(s.is_valid())

    def test_is_active_false_accepted(self):
        s = SkillUpdateSerializer(data={"is_active": False})
        self.assertTrue(s.is_valid())

    def test_all_fields_together(self):
        s = SkillUpdateSerializer(
            data={"skill": "Updated", "description": "New desc", "is_active": False}
        )
        self.assertTrue(s.is_valid())
