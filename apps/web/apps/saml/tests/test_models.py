from django.db import IntegrityError
from django.test import TestCase

from apps.saml.models import SAML
from apps.users.models import User

PROVIDER_BASE = {
    "idp_entity_id": "https://idp.example.com/entity",
    "idp_sso_url": "https://idp.example.com/sso",
    "idp_x509_cert": "MIICERT...",
    "sp_entity_id": "https://sp.example.com/entity",
    "sp_assertion_url": "https://sp.example.com/acs",
}


def make_provider(name="Test Provider", **overrides):
    return SAML.objects.create(name=name, **{**PROVIDER_BASE, **overrides})


class SAMLModelCodeTest(TestCase):
    def test_code_auto_generated_with_saml_prefix(self):
        provider = make_provider()
        self.assertTrue(provider.code.startswith("SAML-"))

    def test_code_contains_primary_key(self):
        provider = make_provider()
        self.assertEqual(provider.code, f"SAML-{provider.pk}")

    def test_each_provider_gets_unique_code(self):
        p1 = make_provider(name="Provider One")
        p2 = make_provider(name="Provider Two")
        self.assertNotEqual(p1.code, p2.code)


class SAMLModelFieldsTest(TestCase):
    def test_str_returns_name(self):
        provider = make_provider(name="My SAML IdP")
        self.assertEqual(str(provider), "My SAML IdP")

    def test_is_active_defaults_to_true(self):
        provider = make_provider()
        self.assertTrue(provider.is_active)

    def test_is_active_can_be_set_false(self):
        provider = make_provider(is_active=False)
        self.assertFalse(provider.is_active)

    def test_sp_entity_id_can_be_blank(self):
        provider = make_provider(sp_entity_id="")
        self.assertEqual(provider.sp_entity_id, "")

    def test_created_at_is_set_on_creation(self):
        provider = make_provider()
        self.assertIsNotNone(provider.created_at)

    def test_updated_at_is_set_on_creation(self):
        provider = make_provider()
        self.assertIsNotNone(provider.updated_at)


class SAMLModelConstraintsTest(TestCase):
    def test_name_unique_constraint_enforced(self):
        make_provider(name="Duplicate Name")
        with self.assertRaises(IntegrityError):
            make_provider(name="Duplicate Name")

    def test_different_names_are_allowed(self):
        p1 = make_provider(name="Provider A")
        p2 = make_provider(name="Provider B")
        self.assertNotEqual(p1.pk, p2.pk)


class SAMLModelAuditTest(TestCase):
    def test_created_by_can_be_set(self):
        user = User.objects.create_user(
            username="admin@example.com", email="admin@example.com", password="pass"
        )
        provider = make_provider(created_by=user)
        self.assertEqual(provider.created_by, user)

    def test_created_by_defaults_to_none(self):
        provider = make_provider()
        self.assertIsNone(provider.created_by)
