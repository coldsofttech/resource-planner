from django.db import IntegrityError
from django.test import TestCase

from apps.contacts.models import Contact
from apps.projects.models import ProjectContact
from apps.projects.tests.factories import (
    make_contact,
    make_project,
    make_project_contact,
)


class ContactCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        contact = make_contact()
        self.assertTrue(contact.code.startswith("CONT-"))

    def test_code_contains_pk(self):
        contact = make_contact()
        self.assertEqual(contact.code, f"CONT-{contact.pk}")

    def test_codes_are_unique(self):
        c1 = make_contact(name="Alice", email="a@example.com")
        c2 = make_contact(name="Bob", email="b@example.com")
        self.assertNotEqual(c1.code, c2.code)


class ContactFieldDefaultsTest(TestCase):
    def setUp(self):
        self.contact = make_contact()

    def test_str_returns_name(self):
        self.assertEqual(str(self.contact), self.contact.name)

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.contact.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.contact.updated_at)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.contact.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.contact.updated_by)

    def test_name_is_stored(self):
        self.assertEqual(self.contact.name, "Test Contact")

    def test_email_is_stored(self):
        self.assertEqual(self.contact.email, "contact@example.com")

    def test_email_can_be_blank(self):
        contact = make_contact(name="No Email", email="")
        self.assertEqual(contact.email, "")


class ContactUniqueConstraintTest(TestCase):
    def test_duplicate_name_and_email_raises_integrity_error(self):
        make_contact(name="Alice", email="alice@example.com")
        with self.assertRaises(IntegrityError):
            make_contact(name="Alice", email="alice@example.com")

    def test_same_name_different_email_is_allowed(self):
        c1 = make_contact(name="Alice", email="a1@example.com")
        c2 = make_contact(name="Alice", email="a2@example.com")
        self.assertNotEqual(c1.pk, c2.pk)

    def test_same_email_different_name_is_allowed(self):
        c1 = make_contact(name="Alice", email="shared@example.com")
        c2 = make_contact(name="Bob", email="shared@example.com")
        self.assertNotEqual(c1.pk, c2.pk)


class ProjectContactCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        pc = make_project_contact()
        self.assertTrue(pc.code.startswith("PROJCT-"))

    def test_code_contains_pk(self):
        pc = make_project_contact()
        self.assertEqual(pc.code, f"PROJCT-{pc.pk}")

    def test_codes_are_unique(self):
        project = make_project("Code Unique Project")
        pc1 = make_project_contact(
            project=project, contact=make_contact(name="A", email="a@example.com")
        )
        pc2 = make_project_contact(
            project=project, contact=make_contact(name="B", email="b@example.com")
        )
        self.assertNotEqual(pc1.code, pc2.code)


class ProjectContactFieldDefaultsTest(TestCase):
    def setUp(self):
        self.pc = make_project_contact()

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.pc.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.pc.updated_at)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.pc.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.pc.updated_by)

    def test_role_is_stored(self):
        self.assertEqual(self.pc.role, "project")


class ProjectContactRelationshipsTest(TestCase):
    def test_project_fk_set(self):
        project = make_project("FK Project")
        pc = make_project_contact(project=project)
        self.assertEqual(pc.project_id, project.pk)

    def test_contact_fk_set(self):
        contact = make_contact(name="FK Contact", email="fk@example.com")
        pc = make_project_contact(contact=contact)
        self.assertEqual(pc.contact_id, contact.pk)

    def test_cascade_delete_when_project_deleted(self):
        project = make_project("Cascade Project")
        pc = make_project_contact(project=project)
        pk = pc.pk
        project.delete()
        self.assertFalse(ProjectContact.objects.filter(pk=pk).exists())

    def test_cascade_delete_when_contact_deleted(self):
        contact = make_contact(name="Cascade Contact", email="cascade@example.com")
        pc = make_project_contact(contact=contact)
        pk = pc.pk
        contact.delete()
        self.assertFalse(ProjectContact.objects.filter(pk=pk).exists())

    def test_reverse_relation_from_project(self):
        project = make_project("Reverse Project")
        make_project_contact(
            project=project, contact=make_contact(name="A", email="a@example.com")
        )
        make_project_contact(
            project=project, contact=make_contact(name="B", email="b@example.com")
        )
        self.assertEqual(project.contacts.count(), 2)


class ProjectContactUniqueConstraintTest(TestCase):
    def test_duplicate_project_contact_raises_integrity_error(self):
        project = make_project("Dup Project")
        contact = make_contact(name="Dup Contact", email="dup@example.com")
        make_project_contact(project=project, contact=contact)
        with self.assertRaises(IntegrityError):
            make_project_contact(project=project, contact=contact)

    def test_same_contact_on_different_projects_is_allowed(self):
        contact = make_contact(name="Shared", email="shared@example.com")
        p1 = make_project("Project 1")
        p2 = make_project("Project 2")
        pc1 = make_project_contact(project=p1, contact=contact)
        pc2 = make_project_contact(project=p2, contact=contact)
        self.assertNotEqual(pc1.pk, pc2.pk)


class ProjectContactOrderingTest(TestCase):
    def test_ordered_by_contact_name(self):
        project = make_project("Ordering Project")
        make_project_contact(
            project=project, contact=make_contact(name="Zara", email="z@example.com")
        )
        make_project_contact(
            project=project, contact=make_contact(name="Alice", email="al@example.com")
        )
        make_project_contact(
            project=project, contact=make_contact(name="Mike", email="m@example.com")
        )
        names = list(
            ProjectContact.objects.filter(project=project).values_list(
                "contact__name", flat=True
            )
        )
        self.assertEqual(names, sorted(names))


class ContactOrderingTest(TestCase):
    def test_contacts_ordered_by_name(self):
        make_contact(name="Zara", email="z@example.com")
        make_contact(name="Alice", email="a@example.com")
        make_contact(name="Mike", email="m@example.com")
        names = list(Contact.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))
