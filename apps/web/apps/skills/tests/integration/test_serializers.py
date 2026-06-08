from django.test import TestCase

from apps.skills.serializers import SkillDetailSerializer, SkillListSerializer
from apps.skills.tests.factories import make_skill
from apps.users.tests.factories import make_user

# ── SkillListSerializer ───────────────────────────────────────────────────────


class SkillListSerializerOutputTest(TestCase):
    _EXPECTED_FIELDS = frozenset(
        [
            "code",
            "skill",
            "description",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
    )

    def test_all_expected_fields_present(self):
        skill = make_skill("Python")
        data = SkillListSerializer(skill).data
        self.assertEqual(set(data.keys()), self._EXPECTED_FIELDS)

    def test_skill_matches_instance(self):
        skill = make_skill("Python")
        self.assertEqual(SkillListSerializer(skill).data["skill"], "Python")

    def test_code_matches_instance(self):
        skill = make_skill("Python")
        self.assertEqual(SkillListSerializer(skill).data["code"], skill.code)

    def test_is_active_reflects_instance_value(self):
        skill = make_skill("Python", is_active=False)
        self.assertFalse(SkillListSerializer(skill).data["is_active"])

    def test_description_matches_instance(self):
        skill = make_skill("Python", description="Core language")
        self.assertEqual(
            SkillListSerializer(skill).data["description"], "Core language"
        )

    def test_created_by_is_null_when_not_set(self):
        skill = make_skill("Python")
        self.assertIsNone(SkillListSerializer(skill).data["created_by"])

    def test_created_by_is_populated_when_set(self):
        user = make_user()
        skill = make_skill("Python")
        skill.created_by = user
        skill.save(update_fields=["created_by"])
        self.assertIsNotNone(SkillListSerializer(skill).data["created_by"])


# ── SkillDetailSerializer ─────────────────────────────────────────────────────


class SkillDetailSerializerOutputTest(TestCase):
    _EXPECTED_FIELDS = frozenset(
        [
            "code",
            "skill",
            "description",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
    )

    def test_all_expected_fields_present(self):
        skill = make_skill("Python")
        data = SkillDetailSerializer(skill).data
        self.assertEqual(set(data.keys()), self._EXPECTED_FIELDS)

    def test_skill_matches_instance(self):
        skill = make_skill("Python")
        self.assertEqual(SkillDetailSerializer(skill).data["skill"], "Python")

    def test_is_active_matches_instance(self):
        skill = make_skill("Python", is_active=True)
        self.assertTrue(SkillDetailSerializer(skill).data["is_active"])

    def test_description_matches_instance(self):
        skill = make_skill("Python", description="Core language")
        self.assertEqual(
            SkillDetailSerializer(skill).data["description"], "Core language"
        )

    def test_created_by_is_null_when_not_set(self):
        skill = make_skill("Python")
        self.assertIsNone(SkillDetailSerializer(skill).data["created_by"])
