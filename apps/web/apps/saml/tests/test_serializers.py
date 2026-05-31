from django.test import TestCase

from apps.saml.models import SAML
from apps.saml.serializers import SAMLCreateSerializer, SAMLSerializer

VALID_DATA = {
    "name": "My SAML IdP",
    "idp_entity_id": "https://idp.example.com/entity",
    "idp_sso_url": "https://idp.example.com/sso",
    "idp_x509_cert": "MIICERT...",
    "sp_entity_id": "https://sp.example.com/entity",
    "sp_assertion_url": "https://sp.example.com/acs",
}

PROVIDER_BASE = {
    "idp_entity_id": "https://idp.example.com/entity",
    "idp_sso_url": "https://idp.example.com/sso",
    "idp_x509_cert": "MIICERT...",
    "sp_entity_id": "https://sp.example.com/entity",
    "sp_assertion_url": "https://sp.example.com/acs",
}


def make_provider(name="Test Provider", **overrides):
    return SAML.objects.create(name=name, **{**PROVIDER_BASE, **overrides})


class SAMLCreateSerializerValidationTest(TestCase):
    def test_valid_data_passes(self):
        s = SAMLCreateSerializer(data=VALID_DATA)
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_name_fails(self):
        data = {**VALID_DATA}
        del data["name"]
        s = SAMLCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_missing_idp_entity_id_fails(self):
        data = {**VALID_DATA}
        del data["idp_entity_id"]
        s = SAMLCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("idp_entity_id", s.errors)

    def test_missing_idp_sso_url_fails(self):
        data = {**VALID_DATA}
        del data["idp_sso_url"]
        s = SAMLCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("idp_sso_url", s.errors)

    def test_missing_idp_x509_cert_fails(self):
        data = {**VALID_DATA}
        del data["idp_x509_cert"]
        s = SAMLCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("idp_x509_cert", s.errors)

    def test_missing_sp_assertion_url_fails(self):
        data = {**VALID_DATA}
        del data["sp_assertion_url"]
        s = SAMLCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("sp_assertion_url", s.errors)

    def test_sp_entity_id_is_optional(self):
        data = {**VALID_DATA}
        del data["sp_entity_id"]
        s = SAMLCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_sp_entity_id_can_be_blank(self):
        data = {**VALID_DATA, "sp_entity_id": ""}
        s = SAMLCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_empty_payload_fails(self):
        s = SAMLCreateSerializer(data={})
        self.assertFalse(s.is_valid())

    def test_non_url_idp_entity_id_fails(self):
        data = {**VALID_DATA, "idp_entity_id": "not-a-url"}
        s = SAMLCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("idp_entity_id", s.errors)


class SAMLSerializerOutputTest(TestCase):
    def test_serializer_includes_all_expected_fields(self):
        provider = make_provider()
        data = SAMLSerializer(provider).data
        expected_fields = [
            "code",
            "name",
            "idp_entity_id",
            "idp_sso_url",
            "idp_x509_cert",
            "sp_entity_id",
            "sp_assertion_url",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_code_reflects_provider_code(self):
        provider = make_provider(name="Code Test Provider")
        data = SAMLSerializer(provider).data
        self.assertEqual(data["code"], provider.code)

    def test_is_active_true_by_default(self):
        provider = make_provider()
        data = SAMLSerializer(provider).data
        self.assertTrue(data["is_active"])

    def test_is_active_false_for_inactive_provider(self):
        provider = make_provider(is_active=False)
        data = SAMLSerializer(provider).data
        self.assertFalse(data["is_active"])

    def test_name_reflects_provider_name(self):
        provider = make_provider(name="My SAML Provider")
        data = SAMLSerializer(provider).data
        self.assertEqual(data["name"], "My SAML Provider")
