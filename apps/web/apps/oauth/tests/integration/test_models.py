from django.db import IntegrityError
from django.test import TestCase

from apps.oauth.tests.factories import make_provider, make_user

# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------


class OAuthModelCodeTest(TestCase):
    def test_code_auto_generated_with_oauth_prefix(self):
        provider = make_provider()
        self.assertTrue(provider.code.startswith("OAUTH-"))

    def test_code_contains_primary_key(self):
        provider = make_provider()
        self.assertEqual(provider.code, f"OAUTH-{provider.pk}")

    def test_each_provider_gets_unique_code(self):
        p1 = make_provider(name="Provider One")
        p2 = make_provider(name="Provider Two")
        self.assertNotEqual(p1.code, p2.code)


# ---------------------------------------------------------------------------
# Field defaults and behaviour
# ---------------------------------------------------------------------------


class OAuthModelFieldsTest(TestCase):
    def test_str_returns_name(self):
        provider = make_provider(name="My IdP")
        self.assertEqual(str(provider), "My IdP")

    def test_is_active_defaults_to_true(self):
        provider = make_provider()
        self.assertTrue(provider.is_active)

    def test_is_active_can_be_set_false(self):
        provider = make_provider(is_active=False)
        self.assertFalse(provider.is_active)

    def test_created_at_is_set_on_creation(self):
        provider = make_provider()
        self.assertIsNotNone(provider.created_at)

    def test_updated_at_is_set_on_creation(self):
        provider = make_provider()
        self.assertIsNotNone(provider.updated_at)

    def test_icon_defaults_to_empty_string(self):
        provider = make_provider()
        self.assertEqual(provider.icon, "")

    def test_icon_can_be_set(self):
        provider = make_provider(icon="bi-shield-lock")
        self.assertEqual(provider.icon, "bi-shield-lock")


# ---------------------------------------------------------------------------
# Uniqueness constraints
# ---------------------------------------------------------------------------


class OAuthModelConstraintsTest(TestCase):
    def test_name_unique_constraint_enforced(self):
        make_provider(name="Duplicate Name")
        with self.assertRaises(IntegrityError):
            make_provider(name="Duplicate Name")

    def test_different_names_are_allowed(self):
        p1 = make_provider(name="Provider A")
        p2 = make_provider(name="Provider B")
        self.assertNotEqual(p1.pk, p2.pk)


# ---------------------------------------------------------------------------
# Audit fields
# ---------------------------------------------------------------------------


class OAuthModelAuditTest(TestCase):
    def test_created_by_can_be_set(self):
        user = make_user(email="admin@example.com")
        provider = make_provider(created_by=user)
        self.assertEqual(provider.created_by, user)

    def test_created_by_defaults_to_none(self):
        provider = make_provider()
        self.assertIsNone(provider.created_by)
