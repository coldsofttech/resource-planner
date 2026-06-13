from django.db import IntegrityError
from django.test import TestCase

from apps.roles.models import Role
from apps.roles.tests.factories import make_role
from apps.users.tests.factories import make_user

# ── Code assignment ───────────────────────────────────────────────────────────


class RoleCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        role = make_role()
        self.assertTrue(role.code.startswith("ROLE-"))

    def test_code_contains_pk(self):
        role = make_role()
        self.assertEqual(role.code, f"ROLE-{role.pk}")

    def test_codes_are_unique(self):
        r1 = make_role("Developer")
        r2 = make_role("Designer")
        self.assertNotEqual(r1.code, r2.code)


# ── Field defaults ────────────────────────────────────────────────────────────


class RoleFieldDefaultTest(TestCase):
    def test_is_active_defaults_to_true(self):
        role = make_role()
        self.assertTrue(role.is_active)

    def test_is_default_defaults_to_false(self):
        role = make_role()
        self.assertFalse(role.is_default)

    def test_is_assignable_defaults_to_false(self):
        role = make_role()
        self.assertFalse(role.is_assignable)

    def test_is_leadership_defaults_to_false(self):
        role = make_role()
        self.assertFalse(role.is_leadership)

    def test_str_returns_role_name(self):
        role = make_role("Developer")
        self.assertEqual(str(role), "Developer")

    def test_stores_role_name(self):
        role = make_role("Product Manager")
        self.assertEqual(role.role, "Product Manager")

    def test_is_assignable_can_be_set_true(self):
        role = make_role(is_assignable=True)
        self.assertTrue(role.is_assignable)

    def test_is_leadership_can_be_set_true(self):
        role = make_role(is_leadership=True)
        self.assertTrue(role.is_leadership)


# ── Constraints ───────────────────────────────────────────────────────────────


class RoleConstraintTest(TestCase):
    def test_duplicate_role_name_raises_integrity_error(self):
        make_role("Developer")
        with self.assertRaises(IntegrityError):
            make_role("Developer")

    def test_different_role_names_are_allowed(self):
        make_role("Developer")
        role = make_role("Designer")
        self.assertIsNotNone(role.pk)


# ── Ordering ──────────────────────────────────────────────────────────────────


class RoleOrderingTest(TestCase):
    def test_ordered_alphabetically_by_role(self):
        make_role("Tester")
        make_role("Analyst")
        make_role("Developer")
        roles = list(Role.objects.values_list("role", flat=True))
        self.assertEqual(roles, sorted(roles))


# ── Auditable fields ──────────────────────────────────────────────────────────


class RoleAuditableTest(TestCase):
    def test_created_at_is_set(self):
        role = make_role()
        self.assertIsNotNone(role.created_at)

    def test_updated_at_is_set(self):
        role = make_role()
        self.assertIsNotNone(role.updated_at)

    def test_created_by_nullable(self):
        role = make_role()
        self.assertIsNone(role.created_by)

    def test_updated_by_nullable(self):
        role = make_role()
        self.assertIsNone(role.updated_by)

    def test_created_by_stores_user(self):
        user = make_user()
        role = Role.objects.create(role="Developer", created_by=user, updated_by=user)
        self.assertEqual(role.created_by, user)
