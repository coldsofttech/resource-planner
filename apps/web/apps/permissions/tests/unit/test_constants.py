from django.test import SimpleTestCase

from apps.permissions.constants import PermissionScope

# ── PermissionScope values ────────────────────────────────────────────────────


class PermissionScopeValuesTest(SimpleTestCase):
    def test_none_is_zero(self):
        self.assertEqual(PermissionScope.NONE, 0)

    def test_self_is_one(self):
        self.assertEqual(PermissionScope.SELF, 1)

    def test_team_is_two(self):
        self.assertEqual(PermissionScope.TEAM, 2)

    def test_all_is_three(self):
        self.assertEqual(PermissionScope.ALL, 3)


# ── PermissionScope labels ────────────────────────────────────────────────────


class PermissionScopeLabelsTest(SimpleTestCase):
    def test_none_label(self):
        self.assertEqual(PermissionScope.NONE.label, "None")

    def test_self_label(self):
        self.assertEqual(PermissionScope.SELF.label, "Self")

    def test_team_label(self):
        self.assertEqual(PermissionScope.TEAM.label, "Team")

    def test_all_label(self):
        self.assertEqual(PermissionScope.ALL.label, "All")


# ── PermissionScope choices ───────────────────────────────────────────────────


class PermissionScopeChoicesTest(SimpleTestCase):
    def test_choices_has_four_entries(self):
        self.assertEqual(len(PermissionScope.choices), 4)

    def test_choices_contains_none(self):
        values = [v for v, _ in PermissionScope.choices]
        self.assertIn(0, values)

    def test_choices_contains_self(self):
        values = [v for v, _ in PermissionScope.choices]
        self.assertIn(1, values)

    def test_choices_contains_team(self):
        values = [v for v, _ in PermissionScope.choices]
        self.assertIn(2, values)

    def test_choices_contains_all(self):
        values = [v for v, _ in PermissionScope.choices]
        self.assertIn(3, values)


# ── PermissionScope ordering ──────────────────────────────────────────────────


class PermissionScopeOrderingTest(SimpleTestCase):
    def test_none_is_least_permissive(self):
        self.assertLess(PermissionScope.NONE, PermissionScope.SELF)

    def test_self_is_less_than_team(self):
        self.assertLess(PermissionScope.SELF, PermissionScope.TEAM)

    def test_team_is_less_than_all(self):
        self.assertLess(PermissionScope.TEAM, PermissionScope.ALL)

    def test_all_is_most_permissive(self):
        self.assertGreater(PermissionScope.ALL, PermissionScope.NONE)

    def test_max_of_none_and_all_is_all(self):
        result = max(PermissionScope.NONE, PermissionScope.ALL)
        self.assertEqual(result, PermissionScope.ALL)

    def test_max_of_self_and_team_is_team(self):
        result = max(PermissionScope.SELF, PermissionScope.TEAM)
        self.assertEqual(result, PermissionScope.TEAM)
