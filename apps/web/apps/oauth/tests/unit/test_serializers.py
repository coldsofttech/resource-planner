from django.test import SimpleTestCase

from apps.oauth.serializers import OAuthCreateSerializer

VALID_DATA = {
    "name": "My IdP",
    "client_id": "cid-123",
    "client_secret": "csecret-456",
    "auth_endpoint": "https://idp.example.com/auth",
    "token_endpoint": "https://idp.example.com/token",
    "userinfo_endpoint": "https://idp.example.com/userinfo",
    "scope": "openid email profile",
}


# ---------------------------------------------------------------------------
# OAuthCreateSerializer — required field validation
# ---------------------------------------------------------------------------


class OAuthCreateSerializerValidationTest(SimpleTestCase):
    def test_valid_data_passes(self):
        s = OAuthCreateSerializer(data=VALID_DATA)
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_name_fails(self):
        data = {**VALID_DATA}
        del data["name"]
        s = OAuthCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_empty_string_name_fails(self):
        s = OAuthCreateSerializer(data={**VALID_DATA, "name": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_missing_client_id_fails(self):
        data = {**VALID_DATA}
        del data["client_id"]
        s = OAuthCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("client_id", s.errors)

    def test_empty_string_client_id_fails(self):
        s = OAuthCreateSerializer(data={**VALID_DATA, "client_id": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("client_id", s.errors)

    def test_missing_client_secret_fails(self):
        data = {**VALID_DATA}
        del data["client_secret"]
        s = OAuthCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("client_secret", s.errors)

    def test_empty_string_client_secret_fails(self):
        s = OAuthCreateSerializer(data={**VALID_DATA, "client_secret": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("client_secret", s.errors)

    def test_missing_auth_endpoint_fails(self):
        data = {**VALID_DATA}
        del data["auth_endpoint"]
        s = OAuthCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("auth_endpoint", s.errors)

    def test_missing_token_endpoint_fails(self):
        data = {**VALID_DATA}
        del data["token_endpoint"]
        s = OAuthCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("token_endpoint", s.errors)

    def test_missing_userinfo_endpoint_fails(self):
        data = {**VALID_DATA}
        del data["userinfo_endpoint"]
        s = OAuthCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("userinfo_endpoint", s.errors)

    def test_missing_scope_fails(self):
        data = {**VALID_DATA}
        del data["scope"]
        s = OAuthCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("scope", s.errors)

    def test_empty_string_scope_fails(self):
        s = OAuthCreateSerializer(data={**VALID_DATA, "scope": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("scope", s.errors)

    def test_empty_payload_fails(self):
        s = OAuthCreateSerializer(data={})
        self.assertFalse(s.is_valid())

    def test_icon_is_optional(self):
        data = {k: v for k, v in VALID_DATA.items()}
        s = OAuthCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_icon_defaults_to_empty_string_when_omitted(self):
        s = OAuthCreateSerializer(data=VALID_DATA)
        s.is_valid()
        self.assertEqual(s.validated_data.get("icon"), "")

    def test_icon_accepts_blank_string(self):
        s = OAuthCreateSerializer(data={**VALID_DATA, "icon": ""})
        self.assertTrue(s.is_valid(), s.errors)

    def test_icon_accepts_value(self):
        s = OAuthCreateSerializer(data={**VALID_DATA, "icon": "bi-shield-lock"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["icon"], "bi-shield-lock")


# ---------------------------------------------------------------------------
# OAuthCreateSerializer — write-only security
# ---------------------------------------------------------------------------


class OAuthCreateSerializerSecurityTest(SimpleTestCase):
    def test_client_secret_is_write_only(self):
        s = OAuthCreateSerializer(data=VALID_DATA)
        s.is_valid()
        self.assertNotIn("client_secret", s.data)

    def test_validated_data_contains_all_required_fields(self):
        s = OAuthCreateSerializer(data=VALID_DATA)
        s.is_valid()
        for field in [
            "name",
            "client_id",
            "client_secret",
            "auth_endpoint",
            "token_endpoint",
            "userinfo_endpoint",
            "scope",
        ]:
            self.assertIn(field, s.validated_data)
