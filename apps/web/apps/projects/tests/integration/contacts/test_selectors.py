from django.test import TestCase

from apps.projects.selectors.contact import (
    get_all_project_contacts,
    get_contact_by_name_and_email,
    get_project_contact_by_code,
    project_contact_exists,
)
from apps.projects.tests.factories import (
    make_contact,
    make_project,
    make_project_contact,
)


class GetAllProjectContactsTest(TestCase):
    def setUp(self):
        self.project = make_project("Selector Project")
        self.contact_a = make_contact(name="Alice", email="alice@example.com")
        self.contact_z = make_contact(name="Zara", email="zara@example.com")
        self.contact_m = make_contact(name="Mike", email="mike@example.com")
        make_project_contact(project=self.project, contact=self.contact_z)
        make_project_contact(project=self.project, contact=self.contact_a)
        make_project_contact(project=self.project, contact=self.contact_m)

    def test_returns_all_contacts_for_project(self):
        result = list(get_all_project_contacts(self.project))
        self.assertEqual(len(result), 3)

    def test_ordered_by_contact_name(self):
        result = list(get_all_project_contacts(self.project))
        names = [pc.contact.name for pc in result]
        self.assertEqual(names, sorted(names))

    def test_excludes_other_project_contacts(self):
        other_project = make_project("Other Project")
        other_contact = make_contact(name="Other", email="other@example.com")
        make_project_contact(project=other_project, contact=other_contact)
        result = list(get_all_project_contacts(self.project))
        self.assertEqual(len(result), 3)

    def test_returns_empty_for_project_with_no_contacts(self):
        empty_project = make_project("Empty Project")
        result = list(get_all_project_contacts(empty_project))
        self.assertEqual(result, [])

    def test_select_related_contact_available(self):
        result = list(get_all_project_contacts(self.project))
        for pc in result:
            self.assertIsNotNone(pc.contact.name)


class GetProjectContactByCodeTest(TestCase):
    def setUp(self):
        self.pc = make_project_contact()

    def test_returns_project_contact_for_valid_code(self):
        result = get_project_contact_by_code(self.pc.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, self.pc.pk)

    def test_returns_none_for_unknown_code(self):
        result = get_project_contact_by_code("PROJCT-999999")
        self.assertIsNone(result)

    def test_select_related_project_available(self):
        result = get_project_contact_by_code(self.pc.code)
        self.assertIsNotNone(result.project.code)

    def test_select_related_contact_available(self):
        result = get_project_contact_by_code(self.pc.code)
        self.assertIsNotNone(result.contact.name)


class ProjectContactExistsTest(TestCase):
    def setUp(self):
        self.project = make_project("Exists Project")
        self.contact = make_contact(name="Test", email="test@example.com")
        self.pc = make_project_contact(project=self.project, contact=self.contact)

    def test_returns_true_when_exists(self):
        self.assertTrue(project_contact_exists(self.project, self.contact))

    def test_returns_false_when_not_exists(self):
        other_contact = make_contact(name="Other", email="other@example.com")
        self.assertFalse(project_contact_exists(self.project, other_contact))

    def test_returns_false_when_excluded_by_pk(self):
        self.assertFalse(
            project_contact_exists(self.project, self.contact, exclude_pk=self.pc.pk)
        )

    def test_returns_true_when_exclude_pk_does_not_match(self):
        other_pc = make_project_contact(
            project=self.project,
            contact=make_contact(name="Second", email="second@example.com"),
        )
        self.assertTrue(
            project_contact_exists(self.project, self.contact, exclude_pk=other_pc.pk)
        )

    def test_different_project_returns_false(self):
        other_project = make_project("Other Project")
        self.assertFalse(project_contact_exists(other_project, self.contact))


class GetContactByNameAndEmailTest(TestCase):
    def setUp(self):
        self.contact = make_contact(name="Alice", email="alice@example.com")

    def test_returns_contact_for_exact_match(self):
        result = get_contact_by_name_and_email("Alice", "alice@example.com")
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, self.contact.pk)

    def test_case_insensitive_name_match(self):
        result = get_contact_by_name_and_email("alice", "alice@example.com")
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, self.contact.pk)

    def test_case_insensitive_email_match(self):
        result = get_contact_by_name_and_email("Alice", "ALICE@EXAMPLE.COM")
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, self.contact.pk)

    def test_strips_whitespace_from_name(self):
        result = get_contact_by_name_and_email("  Alice  ", "alice@example.com")
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, self.contact.pk)

    def test_strips_whitespace_from_email(self):
        result = get_contact_by_name_and_email("Alice", "  alice@example.com  ")
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, self.contact.pk)

    def test_returns_none_for_no_match(self):
        result = get_contact_by_name_and_email("Unknown", "unknown@example.com")
        self.assertIsNone(result)

    def test_returns_none_when_name_does_not_match(self):
        result = get_contact_by_name_and_email("Bob", "alice@example.com")
        self.assertIsNone(result)

    def test_returns_none_when_email_does_not_match(self):
        result = get_contact_by_name_and_email("Alice", "other@example.com")
        self.assertIsNone(result)
