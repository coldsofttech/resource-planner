from django.db import IntegrityError
from django.test import TestCase

from apps.projects.models import Programme
from apps.projects.tests.factories import make_programme
from apps.users.tests.factories import make_user


class ProgrammeCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        p = make_programme()
        self.assertTrue(p.code.startswith("PROG-"))

    def test_code_contains_pk(self):
        p = make_programme()
        self.assertEqual(p.code, f"PROG-{p.pk}")

    def test_codes_are_unique(self):
        p1 = make_programme("Alpha")
        p2 = make_programme("Beta")
        self.assertNotEqual(p1.code, p2.code)


class ProgrammeFieldTest(TestCase):
    def test_is_active_defaults_to_true(self):
        p = make_programme()
        self.assertTrue(p.is_active)

    def test_is_protected_defaults_to_false(self):
        p = make_programme()
        self.assertFalse(p.is_protected)

    def test_description_defaults_to_empty(self):
        p = make_programme()
        self.assertEqual(p.description, "")

    def test_str_returns_name(self):
        p = make_programme("Digital Transformation")
        self.assertEqual(str(p), "Digital Transformation")

    def test_description_stores_value(self):
        p = make_programme(description="Strategic initiative")
        self.assertEqual(p.description, "Strategic initiative")

    def test_is_protected_can_be_set(self):
        p = make_programme(is_protected=True)
        self.assertTrue(p.is_protected)


class ProgrammeConstraintTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        make_programme("Alpha")
        with self.assertRaises(IntegrityError):
            make_programme("Alpha")

    def test_different_names_are_allowed(self):
        make_programme("Alpha")
        p2 = make_programme("Beta")
        self.assertIsNotNone(p2.pk)


class ProgrammeOrderingTest(TestCase):
    def test_ordered_by_name(self):
        make_programme("Zeta")
        make_programme("Alpha")
        make_programme("Mu")
        names = list(Programme.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class ProgrammeAuditableTest(TestCase):
    def test_created_at_is_set(self):
        p = make_programme()
        self.assertIsNotNone(p.created_at)

    def test_updated_at_is_set(self):
        p = make_programme()
        self.assertIsNotNone(p.updated_at)

    def test_created_by_nullable(self):
        p = make_programme()
        self.assertIsNone(p.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        p = Programme.objects.create(name="Managed", created_by=user, updated_by=user)
        self.assertEqual(p.created_by, user)
