from django.test import TestCase

from apps.roles import selectors
from apps.roles.tests.factories import make_role

# ── get_all_roles ─────────────────────────────────────────────────────────────


class GetAllRolesTest(TestCase):
    def test_returns_all_roles_regardless_of_status(self):
        make_role("Developer", is_active=True)
        make_role("COBOL Guru", is_active=False)
        self.assertEqual(selectors.get_all_roles().count(), 2)

    def test_returns_empty_when_none(self):
        self.assertEqual(selectors.get_all_roles().count(), 0)


# ── get_active_roles ──────────────────────────────────────────────────────────


class GetActiveRolesTest(TestCase):
    def test_returns_only_active_roles(self):
        make_role("Developer", is_active=True)
        make_role("COBOL Guru", is_active=False)
        qs = selectors.get_active_roles()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().role, "Developer")

    def test_returns_empty_when_no_active_roles(self):
        make_role("COBOL Guru", is_active=False)
        self.assertEqual(selectors.get_active_roles().count(), 0)


# ── get_role_by_code ──────────────────────────────────────────────────────────


class GetRoleByCodeTest(TestCase):
    def test_returns_role_by_code(self):
        role = make_role("Developer")
        result = selectors.get_role_by_code(role.code)
        self.assertEqual(result, role)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_role_by_code("ROLE-9999")
        self.assertIsNone(result)


# ── role_exists ───────────────────────────────────────────────────────────────


class RoleExistsTest(TestCase):
    def test_returns_true_when_role_exists(self):
        make_role("Developer")
        self.assertTrue(selectors.role_exists("Developer"))

    def test_returns_false_when_role_missing(self):
        self.assertFalse(selectors.role_exists("Developer"))

    def test_excludes_own_pk(self):
        role = make_role("Developer")
        self.assertFalse(selectors.role_exists("Developer", exclude_pk=role.pk))

    def test_detects_conflict_on_other_role(self):
        make_role("Developer")
        other = make_role("Designer")
        self.assertTrue(selectors.role_exists("Developer", exclude_pk=other.pk))


# ── get_role_options ──────────────────────────────────────────────────────────


class GetRoleOptionsTest(TestCase):
    def test_returns_only_active_roles(self):
        make_role("Developer", is_active=True)
        make_role("COBOL Guru", is_active=False)
        qs = selectors.get_role_options()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().role, "Developer")

    def test_excludes_inactive_roles(self):
        make_role("COBOL Guru", is_active=False)
        self.assertEqual(selectors.get_role_options().count(), 0)

    def test_returns_empty_when_no_roles(self):
        self.assertEqual(selectors.get_role_options().count(), 0)

    def test_ordered_alphabetically_by_role(self):
        make_role("Tester", is_active=True)
        make_role("Analyst", is_active=True)
        make_role("Developer", is_active=True)
        names = list(selectors.get_role_options().values_list("role", flat=True))
        self.assertEqual(names, sorted(names))

    def test_each_row_exposes_code_and_role(self):
        role = make_role("Developer", is_active=True)
        result = selectors.get_role_options().first()
        self.assertEqual(result.code, role.code)
        self.assertEqual(result.role, role.role)


# ── get_role_stats ────────────────────────────────────────────────────────────


class GetRoleStatsTest(TestCase):
    def test_counts_total_active_and_inactive(self):
        make_role("Developer", is_active=True)
        make_role("Analyst", is_active=True)
        make_role("COBOL Guru", is_active=False)
        stats = selectors.get_role_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)

    def test_returns_zeros_when_no_roles(self):
        stats = selectors.get_role_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["inactive"], 0)
