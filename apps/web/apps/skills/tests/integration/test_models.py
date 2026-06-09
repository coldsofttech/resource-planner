from django.db import IntegrityError
from django.test import TestCase

from apps.skills.models import Skill
from apps.skills.tests.factories import make_skill
from apps.users.tests.factories import make_user

# ── Code assignment ───────────────────────────────────────────────────────────


class SkillCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        skill = make_skill()
        self.assertTrue(skill.code.startswith("SKILL-"))

    def test_code_contains_pk(self):
        skill = make_skill()
        self.assertEqual(skill.code, f"SKILL-{skill.pk}")

    def test_codes_are_unique(self):
        s1 = make_skill("Python")
        s2 = make_skill("Java")
        self.assertNotEqual(s1.code, s2.code)


# ── Field defaults ────────────────────────────────────────────────────────────


class SkillFieldTest(TestCase):
    def test_is_active_defaults_to_true(self):
        skill = make_skill()
        self.assertTrue(skill.is_active)

    def test_description_defaults_to_empty(self):
        skill = make_skill()
        self.assertEqual(skill.description, "")

    def test_str_returns_skill(self):
        skill = make_skill("Python")
        self.assertEqual(str(skill), "Python")

    def test_description_stores_value(self):
        skill = make_skill(description="Core language")
        self.assertEqual(skill.description, "Core language")


# ── Constraints ───────────────────────────────────────────────────────────────


class SkillConstraintTest(TestCase):
    def test_duplicate_skill_raises_integrity_error(self):
        make_skill("Python")
        with self.assertRaises(IntegrityError):
            make_skill("Python")

    def test_different_skills_are_allowed(self):
        make_skill("Python")
        skill = make_skill("Java")
        self.assertIsNotNone(skill.pk)


# ── Ordering ──────────────────────────────────────────────────────────────────


class SkillOrderingTest(TestCase):
    def test_ordered_by_skill(self):
        make_skill("Rust")
        make_skill("Go")
        make_skill("Python")
        skills = list(Skill.objects.values_list("skill", flat=True))
        self.assertEqual(skills, sorted(skills))


# ── Auditable fields ──────────────────────────────────────────────────────────


class SkillAuditableTest(TestCase):
    def test_created_at_is_set(self):
        skill = make_skill()
        self.assertIsNotNone(skill.created_at)

    def test_updated_at_is_set(self):
        skill = make_skill()
        self.assertIsNotNone(skill.updated_at)

    def test_created_by_nullable(self):
        skill = make_skill()
        self.assertIsNone(skill.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        skill = Skill.objects.create(skill="Python", created_by=user, updated_by=user)
        self.assertEqual(skill.created_by, user)
