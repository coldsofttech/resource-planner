from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.models import Configuration
from apps.users.models import User
from apps.users.tests.factories import make_user

META_URL = "/api/v1/meta/"

_PUBLIC_META = {
    "app_name": "TestApp",
    "auth_mode": "classic",
    "allow_registration": True,
}

_USER_META = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "is_superuser": False,
}

_OAUTH_BASE = {
    "client_id": "cid",
    "client_secret": "csecret",
    "auth_endpoint": "https://idp.example.com/auth",
    "token_endpoint": "https://idp.example.com/token",
    "userinfo_endpoint": "https://idp.example.com/userinfo",
    "scope": "openid email",
}

_SAML_BASE = {
    "idp_entity_id": "https://idp.example.com/entity",
    "idp_sso_url": "https://idp.example.com/sso",
    "idp_x509_cert": "MIICERT...",
    "sp_entity_id": "https://sp.example.com/entity",
    "sp_assertion_url": "https://sp.example.com/acs",
}


# ---------------------------------------------------------------------------
# Unauthenticated — response structure
# ---------------------------------------------------------------------------


class MetaUnauthenticatedTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_returns_200(self, _pub):
        self.assertEqual(self.client.get(META_URL).status_code, 200)

    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_response_success_flag_is_true(self, _pub):
        self.assertTrue(self.client.get(META_URL).data["success"])

    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_response_message(self, _pub):
        self.assertEqual(self.client.get(META_URL).data["message"], "Meta fetched.")

    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_response_contains_app_name(self, _pub):
        self.assertEqual(self.client.get(META_URL).data["data"]["app_name"], "TestApp")

    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_response_contains_auth_mode(self, _pub):
        self.assertEqual(self.client.get(META_URL).data["data"]["auth_mode"], "classic")

    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_response_contains_allow_registration(self, _pub):
        self.assertIn("allow_registration", self.client.get(META_URL).data["data"])

    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_does_not_include_user_when_unauthenticated(self, _pub):
        self.assertNotIn("user", self.client.get(META_URL).data["data"])


# ---------------------------------------------------------------------------
# Authenticated — response structure
# ---------------------------------------------------------------------------


class MetaAuthenticatedTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="jane",
            email="jane@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Doe",
        )
        self.client.force_login(self.user)

    @patch("apps.meta.services.get_user_meta", return_value=_USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_returns_200_when_authenticated(self, _pub, _usr):
        self.assertEqual(self.client.get(META_URL).status_code, 200)

    @patch("apps.meta.services.get_user_meta", return_value=_USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_includes_user_when_authenticated(self, _pub, _usr):
        self.assertIn("user", self.client.get(META_URL).data["data"])

    @patch("apps.meta.services.get_user_meta", return_value=_USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_user_contains_name(self, _pub, _usr):
        self.assertEqual(
            self.client.get(META_URL).data["data"]["user"]["name"], "Jane Doe"
        )

    @patch("apps.meta.services.get_user_meta", return_value=_USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_user_contains_email(self, _pub, _usr):
        self.assertEqual(
            self.client.get(META_URL).data["data"]["user"]["email"], "jane@example.com"
        )

    @patch("apps.meta.services.get_user_meta", return_value=_USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_user_contains_is_superuser(self, _pub, _usr):
        self.assertIn("is_superuser", self.client.get(META_URL).data["data"]["user"])

    @patch("apps.meta.services.get_user_meta", return_value=_USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_does_not_expose_password_in_user(self, _pub, _usr):
        self.assertNotIn(
            "password", self.client.get(META_URL).data["data"].get("user", {})
        )

    @patch(
        "apps.meta.services.get_user_meta",
        return_value={**_USER_META, "is_superuser": True},
    )
    @patch("apps.meta.services.get_public_meta", return_value=_PUBLIC_META)
    def test_meta_reflects_superuser_flag(self, _pub, _usr):
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(self.client.get(META_URL).data["data"]["user"]["is_superuser"])


# ---------------------------------------------------------------------------
# HTTP method enforcement
# ---------------------------------------------------------------------------


class MetaMethodEnforcementTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_returns_405(self):
        self.assertEqual(self.client.post(META_URL, {}).status_code, 405)

    def test_put_returns_405(self):
        self.assertEqual(self.client.put(META_URL, {}).status_code, 405)

    def test_patch_returns_405(self):
        self.assertEqual(self.client.patch(META_URL, {}).status_code, 405)

    def test_delete_returns_405(self):
        self.assertEqual(self.client.delete(META_URL).status_code, 405)


# ---------------------------------------------------------------------------
# Provider fields in API response (real DB — no mocks)
# ---------------------------------------------------------------------------


class MetaAPIClassicModeProviderFieldsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="classic")

    def test_oauth_provider_is_null_in_classic_mode(self):
        self.assertIsNone(self.client.get(META_URL).data["data"]["oauth_provider"])

    def test_saml_provider_is_null_in_classic_mode(self):
        self.assertIsNone(self.client.get(META_URL).data["data"]["saml_provider"])


class MetaAPIProviderFieldsOAuthModeTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="oauth")

    def test_oauth_provider_is_not_null_when_active_provider_exists(self):
        from apps.oauth.models import OAuth

        OAuth.objects.create(name="Test OAuth", is_active=True, **_OAUTH_BASE)
        self.assertIsNotNone(self.client.get(META_URL).data["data"]["oauth_provider"])

    def test_oauth_provider_contains_code_name_icon(self):
        from apps.oauth.models import OAuth

        OAuth.objects.create(name="Test OAuth", is_active=True, **_OAUTH_BASE)
        provider = self.client.get(META_URL).data["data"]["oauth_provider"]
        for key in ("code", "name", "icon"):
            self.assertIn(key, provider)

    def test_saml_provider_is_null_in_oauth_mode(self):
        self.assertIsNone(self.client.get(META_URL).data["data"]["saml_provider"])

    def test_oauth_provider_is_null_when_no_active_provider(self):
        self.assertIsNone(self.client.get(META_URL).data["data"]["oauth_provider"])


class MetaAPIProviderFieldsSAMLModeTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")

    def test_saml_provider_is_not_null_when_active_provider_exists(self):
        from apps.saml.models import SAML

        SAML.objects.create(name="Test SAML", is_active=True, **_SAML_BASE)
        self.assertIsNotNone(self.client.get(META_URL).data["data"]["saml_provider"])

    def test_saml_provider_contains_code_name_icon(self):
        from apps.saml.models import SAML

        SAML.objects.create(name="Test SAML", is_active=True, **_SAML_BASE)
        provider = self.client.get(META_URL).data["data"]["saml_provider"]
        for key in ("code", "name", "icon"):
            self.assertIn(key, provider)

    def test_oauth_provider_is_null_in_saml_mode(self):
        self.assertIsNone(self.client.get(META_URL).data["data"]["oauth_provider"])

    def test_saml_provider_is_null_when_no_active_provider(self):
        self.assertIsNone(self.client.get(META_URL).data["data"]["saml_provider"])


# ---------------------------------------------------------------------------
# Unauthenticated — provider fields accessible without login
# ---------------------------------------------------------------------------


class MetaAPIProviderFieldsUnauthenticatedTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_provider_fields_accessible_without_authentication(self):
        response = self.client.get(META_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("oauth_provider", response.data["data"])
        self.assertIn("saml_provider", response.data["data"])

    def test_authenticated_user_not_required_for_provider_fields(self):
        user = make_user()
        self.client.force_login(user)
        response = self.client.get(META_URL)
        self.assertIn("oauth_provider", response.data["data"])
        self.assertIn("saml_provider", response.data["data"])
