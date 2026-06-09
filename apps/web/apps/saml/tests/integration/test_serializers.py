from django.test import TestCase

from apps.saml.serializers import SAMLSerializer
from apps.saml.tests.factories import make_provider


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
            "icon",
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

    def test_icon_is_empty_string_by_default(self):
        provider = make_provider()
        data = SAMLSerializer(provider).data
        self.assertEqual(data["icon"], "")

    def test_sp_entity_id_is_present_in_output(self):
        provider = make_provider(sp_entity_id="https://sp.example.com/entity")
        data = SAMLSerializer(provider).data
        self.assertEqual(data["sp_entity_id"], "https://sp.example.com/entity")

    def test_sp_entity_id_blank_is_serialized_as_empty_string(self):
        provider = make_provider(sp_entity_id="")
        data = SAMLSerializer(provider).data
        self.assertEqual(data["sp_entity_id"], "")

    def test_created_by_is_none_when_not_set(self):
        provider = make_provider()
        data = SAMLSerializer(provider).data
        self.assertIsNone(data["created_by"])
