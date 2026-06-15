from django.db import IntegrityError
from django.test import TestCase

from apps.projects.models import ProjectType
from apps.projects.tests.factories import make_project_type
from apps.users.tests.factories import make_user


class ProjectTypeCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        pt = make_project_type()
        self.assertTrue(pt.code.startswith("PROJTYPE-"))

    def test_code_contains_pk(self):
        pt = make_project_type()
        self.assertEqual(pt.code, f"PROJTYPE-{pt.pk}")

    def test_codes_are_unique(self):
        pt1 = make_project_type("Alpha")
        pt2 = make_project_type("Beta")
        self.assertNotEqual(pt1.code, pt2.code)


class ProjectTypeFieldTest(TestCase):
    def test_is_active_defaults_to_true(self):
        pt = make_project_type()
        self.assertTrue(pt.is_active)

    def test_is_protected_defaults_to_false(self):
        pt = make_project_type()
        self.assertFalse(pt.is_protected)

    def test_description_defaults_to_empty(self):
        pt = make_project_type()
        self.assertEqual(pt.description, "")

    def test_str_returns_name(self):
        pt = make_project_type("Internal")
        self.assertEqual(str(pt), "Internal")

    def test_description_stores_value(self):
        pt = make_project_type(description="An internal classification")
        self.assertEqual(pt.description, "An internal classification")

    def test_is_protected_can_be_set(self):
        pt = make_project_type(is_protected=True)
        self.assertTrue(pt.is_protected)

    def test_is_active_can_be_set_to_false(self):
        pt = make_project_type(is_active=False)
        self.assertFalse(pt.is_active)


class ProjectTypeConstraintTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        make_project_type("Alpha")
        with self.assertRaises(IntegrityError):
            make_project_type("Alpha")

    def test_different_names_are_allowed(self):
        make_project_type("Alpha")
        pt2 = make_project_type("Beta")
        self.assertIsNotNone(pt2.pk)


class ProjectTypeOrderingTest(TestCase):
    def test_ordered_by_name(self):
        make_project_type("Zeta")
        make_project_type("Alpha")
        make_project_type("Mu")
        names = list(ProjectType.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class ProjectTypeAuditableTest(TestCase):
    def test_created_at_is_set(self):
        pt = make_project_type()
        self.assertIsNotNone(pt.created_at)

    def test_updated_at_is_set(self):
        pt = make_project_type()
        self.assertIsNotNone(pt.updated_at)

    def test_created_by_nullable(self):
        pt = make_project_type()
        self.assertIsNone(pt.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        pt = ProjectType.objects.create(
            name="Managed", created_by=user, updated_by=user
        )
        self.assertEqual(pt.created_by, user)
