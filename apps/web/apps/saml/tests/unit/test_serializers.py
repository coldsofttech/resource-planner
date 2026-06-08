from django.test import SimpleTestCase

from apps.saml.serializers import SAMLCreateSerializer

VALID_DATA = {
    "name": "My SAML IdP",
    "idp_entity_id": "https://idp.example.com/entity",
    "idp_sso_url": "https://idp.example.com/sso",
    "idp_x509_cert": "MIICERT...",
    "sp_entity_id": "https://sp.example.com/entity",
    "sp_assertion_url": "https://sp.example.com/acs",
}


class SAMLCreateSerializerValidationTest(SimpleTestCase):
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

    def test_non_url_idp_sso_url_fails(self):
        data = {**VALID_DATA, "idp_sso_url": "not-a-url"}
        s = SAMLCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("idp_sso_url", s.errors)

    def test_non_url_sp_assertion_url_fails(self):
        data = {**VALID_DATA, "sp_assertion_url": "not-a-url"}
        s = SAMLCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("sp_assertion_url", s.errors)

    def test_icon_is_optional(self):
        data = {**VALID_DATA}
        data.pop("icon", None)
        s = SAMLCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_icon_can_be_blank(self):
        s = SAMLCreateSerializer(data={**VALID_DATA, "icon": ""})
        self.assertTrue(s.is_valid(), s.errors)

    def test_icon_defaults_to_empty_string(self):
        s = SAMLCreateSerializer(data={**VALID_DATA})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data.get("icon", ""), "")
