from django.db import IntegrityError
from django.test import TestCase

from apps.employment_types.models import EmploymentType
from apps.employment_types.tests.factories import make_employment_type
from apps.users.tests.factories import make_user

# ── Code assignment ───────────────────────────────────────────────────────────


class EmploymentTypeCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        et = make_employment_type()
        self.assertTrue(et.code.startswith("EMPTYPE-"))

    def test_code_contains_pk(self):
        et = make_employment_type()
        self.assertEqual(et.code, f"EMPTYPE-{et.pk}")

    def test_codes_are_unique(self):
        et1 = make_employment_type("Full-time")
        et2 = make_employment_type("Part-time")
        self.assertNotEqual(et1.code, et2.code)


# ── Field defaults ────────────────────────────────────────────────────────────


class EmploymentTypeFieldTest(TestCase):
    def test_is_active_defaults_to_true(self):
        et = make_employment_type()
        self.assertTrue(et.is_active)

    def test_is_default_defaults_to_false(self):
        et = make_employment_type()
        self.assertFalse(et.is_default)

    def test_str_returns_name(self):
        et = make_employment_type("Full-time")
        self.assertEqual(str(et), "Full-time")

    def test_name_stores_value(self):
        et = make_employment_type("Contract")
        self.assertEqual(et.name, "Contract")

    def test_is_default_stores_true(self):
        et = make_employment_type(is_default=True)
        self.assertTrue(et.is_default)


# ── Constraints ───────────────────────────────────────────────────────────────


class EmploymentTypeConstraintTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        make_employment_type("Full-time")
        with self.assertRaises(IntegrityError):
            make_employment_type("Full-time")

    def test_different_names_are_allowed(self):
        make_employment_type("Full-time")
        et = make_employment_type("Part-time")
        self.assertIsNotNone(et.pk)


# ── Ordering ──────────────────────────────────────────────────────────────────


class EmploymentTypeOrderingTest(TestCase):
    def test_ordered_by_name(self):
        make_employment_type("Part-time")
        make_employment_type("Casual")
        make_employment_type("Full-time")
        names = list(EmploymentType.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


# ── Auditable fields ──────────────────────────────────────────────────────────


class EmploymentTypeAuditableTest(TestCase):
    def test_created_at_is_set(self):
        et = make_employment_type()
        self.assertIsNotNone(et.created_at)

    def test_updated_at_is_set(self):
        et = make_employment_type()
        self.assertIsNotNone(et.updated_at)

    def test_created_by_nullable(self):
        et = make_employment_type()
        self.assertIsNone(et.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        et = EmploymentType.objects.create(
            name="Full-time", created_by=user, updated_by=user
        )
        self.assertEqual(et.created_by, user)
