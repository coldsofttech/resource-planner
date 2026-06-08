from django.test import TestCase

from apps.oauth.serializers import OAuthSerializer
from apps.oauth.tests.factories import make_provider

# ---------------------------------------------------------------------------
# OAuthSerializer — read output
# ---------------------------------------------------------------------------


class OAuthSerializerOutputTest(TestCase):
    def test_serializer_includes_all_expected_fields(self):
        provider = make_provider()
        data = OAuthSerializer(provider).data
        for field in [
            "code",
            "name",
            "client_id",
            "auth_endpoint",
            "token_endpoint",
            "userinfo_endpoint",
            "scope",
            "icon",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]:
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

    def test_icon_included_in_output(self):
        provider = make_provider(icon="bi-shield-lock")
        data = OAuthSerializer(provider).data
        self.assertEqual(data["icon"], "bi-shield-lock")

    def test_icon_empty_string_by_default(self):
        provider = make_provider()
        data = OAuthSerializer(provider).data
        self.assertEqual(data["icon"], "")
