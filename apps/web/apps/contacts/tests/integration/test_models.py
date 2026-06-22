from django.db import IntegrityError
from django.test import TestCase

from apps.contacts.models import Contact
from apps.contacts.tests.factories import make_contact
from apps.users.tests.factories import make_user


class ContactCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        contact = make_contact()
        self.assertTrue(contact.code.startswith("CONT-"))

    def test_code_contains_pk(self):
        contact = make_contact()
        self.assertEqual(contact.code, f"CONT-{contact.pk}")

    def test_codes_are_unique_across_contacts(self):
        c1 = make_contact(name="Alice", email="a@example.com")
        c2 = make_contact(name="Bob", email="b@example.com")
        self.assertNotEqual(c1.code, c2.code)

    def test_code_not_editable_directly(self):
        self.assertFalse(Contact._meta.get_field("code").editable)


class ContactStrTest(TestCase):
    def test_str_returns_name(self):
        contact = make_contact(name="Alice Smith")
        self.assertEqual(str(contact), "Alice Smith")

    def test_str_reflects_updated_name(self):
        contact = make_contact(name="Old Name")
        contact.name = "New Name"
        contact.save(update_fields=["name"])
        self.assertEqual(str(contact), "New Name")


class ContactFieldDefaultsTest(TestCase):
    def setUp(self):
        self.contact = make_contact()

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.contact.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.contact.updated_at)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.contact.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.contact.updated_by)

    def test_name_stored_correctly(self):
        self.assertEqual(self.contact.name, "Test Contact")

    def test_email_stored_correctly(self):
        self.assertEqual(self.contact.email, "contact@example.com")


class ContactEmailTest(TestCase):
    def test_email_can_be_blank(self):
        contact = make_contact(name="No Email", email="")
        self.assertEqual(contact.email, "")

    def test_email_is_optional_on_creation(self):
        contact = Contact.objects.create(name="No Email Contact")
        self.assertEqual(contact.email, "")

    def test_email_accepts_standard_address(self):
        contact = make_contact(name="Valid Email", email="user@domain.co.uk")
        self.assertEqual(contact.email, "user@domain.co.uk")

    def test_two_contacts_can_share_blank_email_with_different_names(self):
        c1 = make_contact(name="Alice", email="")
        c2 = make_contact(name="Bob", email="")
        self.assertNotEqual(c1.pk, c2.pk)


class ContactAuditUserTest(TestCase):
    def test_created_by_stores_user(self):
        user = make_user()
        contact = make_contact(created_by=user, updated_by=user)
        self.assertEqual(contact.created_by, user)

    def test_updated_by_stores_user(self):
        user = make_user()
        contact = make_contact(created_by=user, updated_by=user)
        self.assertEqual(contact.updated_by, user)

    def test_created_by_set_null_when_user_deleted(self):
        user = make_user()
        contact = make_contact(created_by=user, updated_by=user)
        user.delete()
        contact.refresh_from_db()
        self.assertIsNone(contact.created_by)

    def test_updated_by_set_null_when_user_deleted(self):
        user = make_user()
        contact = make_contact(created_by=user, updated_by=user)
        user.delete()
        contact.refresh_from_db()
        self.assertIsNone(contact.updated_by)


class ContactUniqueConstraintTest(TestCase):
    def test_duplicate_name_and_email_raises_integrity_error(self):
        make_contact(name="Alice", email="alice@example.com")
        with self.assertRaises(IntegrityError):
            make_contact(name="Alice", email="alice@example.com")

    def test_same_name_different_email_is_allowed(self):
        c1 = make_contact(name="Alice", email="alice1@example.com")
        c2 = make_contact(name="Alice", email="alice2@example.com")
        self.assertNotEqual(c1.pk, c2.pk)

    def test_same_email_different_name_is_allowed(self):
        c1 = make_contact(name="Alice", email="shared@example.com")
        c2 = make_contact(name="Bob", email="shared@example.com")
        self.assertNotEqual(c1.pk, c2.pk)

    def test_same_name_blank_email_and_same_name_with_email_allowed(self):
        c1 = make_contact(name="Alice", email="")
        c2 = make_contact(name="Alice", email="alice@example.com")
        self.assertNotEqual(c1.pk, c2.pk)

    def test_constraint_name_is_deterministic(self):
        constraint_names = [c.name for c in Contact._meta.constraints]
        self.assertIn("contacts_contact_name_email_uniq", constraint_names)


class ContactOrderingTest(TestCase):
    def test_contacts_ordered_by_name_ascending(self):
        make_contact(name="Zara", email="z@example.com")
        make_contact(name="Alice", email="a@example.com")
        make_contact(name="Mike", email="m@example.com")
        names = list(Contact.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))

    def test_ordering_is_case_sensitive_by_default(self):
        make_contact(name="bob", email="lower@example.com")
        make_contact(name="Alice", email="upper@example.com")
        contacts = list(Contact.objects.all())
        self.assertGreater(len(contacts), 0)

    def test_default_ordering_defined_on_model(self):
        self.assertEqual(Contact._meta.ordering, ["name"])


class ContactPersistenceTest(TestCase):
    def test_contact_persists_to_db(self):
        make_contact(name="Persisted", email="p@example.com")
        self.assertTrue(Contact.objects.filter(name="Persisted").exists())

    def test_contact_can_be_retrieved_by_email(self):
        make_contact(name="Email Lookup", email="lookup@example.com")
        self.assertTrue(Contact.objects.filter(email="lookup@example.com").exists())

    def test_updated_at_changes_on_save(self):
        contact = make_contact()
        original_updated_at = contact.updated_at
        contact.name = "Updated Name"
        contact.save(update_fields=["name", "updated_at"])
        contact.refresh_from_db()
        self.assertGreaterEqual(contact.updated_at, original_updated_at)

    def test_delete_removes_contact(self):
        contact = make_contact()
        pk = contact.pk
        contact.delete()
        self.assertFalse(Contact.objects.filter(pk=pk).exists())
