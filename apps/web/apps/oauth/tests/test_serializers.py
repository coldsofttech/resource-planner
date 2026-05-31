from django.test import TestCase

from apps.oauth.models import OAuth
from apps.oauth.serializers import OAuthCreateSerializer, OAuthSerializer

VALID_DATA = {
    "name": "My IdP",
    "client_id": "cid-123",
    "client_secret": "csecret-456",
    "auth_endpoint": "https://idp.example.com/auth",
    "token_endpoint": "https://idp.example.com/token",
    "userinfo_endpoint": "https://idp.example.com/userinfo",
    "scope": "openid email profile",
}

PROVIDER_BASE = {
    "client_id": "cid",
    "client_secret": "csecret",
    "auth_endpoint": "https://idp.example.com/auth",
    "token_endpoint": "https://idp.example.com/token",
    "userinfo_endpoint": "https://idp.example.com/userinfo",
    "scope": "openid email",
}


def make_provider(name="Test Provider", **overrides):
    return OAuth.objects.create(name=name, **{**PROVIDER_BASE, **overrides})


class OAuthCreateSerializerValidationTest(TestCase):
    def test_valid_data_passes(self):
        s = OAuthCreateSerializer(data=VALID_DATA)
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_name_fails(self):
        data = {**VALID_DATA}
        del data["name"]
        s = OAuthCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_missing_client_id_fails(self):
        data = {**VALID_DATA}
        del data["client_id"]
        s = OAuthCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("client_id", s.errors)

    def test_missing_client_secret_fails(self):
        data = {**VALID_DATA}
        del data["client_secret"]
        s = OAuthCreateSerializer(data=data)
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

    def test_empty_payload_fails(self):
        s = OAuthCreateSerializer(data={})
        self.assertFalse(s.is_valid())


class OAuthCreateSerializerSecurityTest(TestCase):
    def test_client_secret_is_write_only(self):
        s = OAuthCreateSerializer(data=VALID_DATA)
        s.is_valid()
        self.assertNotIn("client_secret", s.data)

    def test_validated_data_contains_all_fields(self):
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


class OAuthSerializerOutputTest(TestCase):
    def test_serializer_includes_all_expected_fields(self):
        provider = make_provider()
        data = OAuthSerializer(provider).data
        expected_fields = [
            "code",
            "name",
            "client_id",
            "auth_endpoint",
            "token_endpoint",
            "userinfo_endpoint",
            "scope",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_client_secret_not_exposed_in_read_serializer(self):
        provider = make_provider()
        data = OAuthSerializer(provider).data
        self.assertNotIn("client_secret", data)

    def test_code_reflects_provider_code(self):
        provider = make_provider(name="Code Test Provider")
        data = OAuthSerializer(provider).data
        self.assertEqual(data["code"], provider.code)

    def test_is_active_true_by_default(self):
        provider = make_provider()
        data = OAuthSerializer(provider).data
        self.assertTrue(data["is_active"])

    def test_is_active_false_for_inactive_provider(self):
        provider = make_provider(is_active=False)
        data = OAuthSerializer(provider).data
        self.assertFalse(data["is_active"])
