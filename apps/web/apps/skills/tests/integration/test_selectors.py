from django.test import TestCase

from apps.skills import selectors
from apps.skills.tests.factories import make_skill


class GetAllSkillsTest(TestCase):
    def test_returns_all_skills(self):
        make_skill("Python")
        make_skill("Java", is_active=False)
        self.assertEqual(selectors.get_all_skills().count(), 2)

    def test_returns_empty_when_none(self):
        self.assertEqual(selectors.get_all_skills().count(), 0)


class GetActiveSkillsTest(TestCase):
    def test_returns_only_active_skills(self):
        make_skill("Python", is_active=True)
        make_skill("Java", is_active=False)
        qs = selectors.get_active_skills()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().skill, "Python")

    def test_returns_empty_when_no_active(self):
        make_skill("Python", is_active=False)
        self.assertEqual(selectors.get_active_skills().count(), 0)


class GetSkillByCodeTest(TestCase):
    def test_returns_skill_by_code(self):
        skill = make_skill("Python")
        result = selectors.get_skill_by_code(skill.code)
        self.assertEqual(result, skill)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_skill_by_code("SKILL-9999")
        self.assertIsNone(result)


class SkillExistsTest(TestCase):
    def test_returns_true_when_skill_exists(self):
        make_skill("Python")
        self.assertTrue(selectors.skill_exists("Python"))

    def test_returns_false_when_skill_missing(self):
        self.assertFalse(selectors.skill_exists("Python"))

    def test_excludes_own_pk(self):
        skill = make_skill("Python")
        self.assertFalse(selectors.skill_exists("Python", exclude_pk=skill.pk))

    def test_detects_conflict_on_other_skill(self):
        make_skill("Python")
        other = make_skill("Java")
        self.assertTrue(selectors.skill_exists("Python", exclude_pk=other.pk))


class GetSkillStatsTest(TestCase):
    def test_stats_counts_correctly(self):
        make_skill("Python", is_active=True)
        make_skill("Java", is_active=True)
        make_skill("COBOL", is_active=False)
        stats = selectors.get_skill_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)

    def test_stats_with_no_skills(self):
        stats = selectors.get_skill_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["inactive"], 0)


class GetSkillOptionsTest(TestCase):
    def test_returns_only_active_skills(self):
        make_skill("Python", is_active=True)
        make_skill("COBOL", is_active=False)
        qs = selectors.get_skill_options()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().skill, "Python")

    def test_excludes_inactive_skills(self):
        make_skill("COBOL", is_active=False)
        self.assertEqual(selectors.get_skill_options().count(), 0)

    def test_returns_empty_when_no_skills(self):
        self.assertEqual(selectors.get_skill_options().count(), 0)

    def test_ordered_alphabetically_by_skill_name(self):
        make_skill("Rust", is_active=True)
        make_skill("Go", is_active=True)
        make_skill("Python", is_active=True)
        names = list(selectors.get_skill_options().values_list("skill", flat=True))
        self.assertEqual(names, sorted(names))

    def test_each_row_exposes_code_and_skill(self):
        skill = make_skill("Python", is_active=True)
        result = selectors.get_skill_options().first()
        self.assertEqual(result.code, skill.code)
        self.assertEqual(result.skill, skill.skill)
