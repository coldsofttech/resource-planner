from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.oauth.models import OAuth

CREATE_URL = "/api/v1/auth/oauth/"
CALLBACK_URL = "/api/v1/auth/oauth/callback/"

PROVIDER_PAYLOAD = {
    "name": "Test IdP",
    "client_id": "my-client-id",
    "client_secret": "my-client-secret",
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


def make_provider(name="Test Provider", is_active=True, **overrides):
    return OAuth.objects.create(
        name=name, is_active=is_active, **{**PROVIDER_BASE, **overrides}
    )


class OAuthCreateAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_returns_201(self, _prefix, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 201)

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_response_success_flag_is_true(self, _prefix, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertTrue(response.data["success"])

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_response_contains_provider_name(self, _prefix, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertEqual(response.data["data"]["name"], "Test IdP")

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_response_contains_oauth_code(self, _prefix, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertTrue(response.data["data"]["code"].startswith("OAUTH-"))

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_does_not_expose_client_secret(self, _prefix, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertNotIn("client_secret", response.data.get("data", {}))

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_duplicate_provider_name_returns_409(self, _prefix, _enc):
        self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 409)

    def test_missing_required_fields_returns_error(self):
        response = self.client.post(CREATE_URL, {"name": "Incomplete"}, format="json")
        self.assertIn(response.status_code, [400, 422])

    def test_empty_payload_returns_error(self):
        response = self.client.post(CREATE_URL, {}, format="json")
        self.assertIn(response.status_code, [400, 422])


class OAuthAuthorizeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _authorize_url(self, provider):
        return f"/api/v1/auth/oauth/{provider.code}/authorize/"

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_authorize_returns_200(self, _dec):
        provider = make_provider(name="Active Provider")
        response = self.client.get(
            self._authorize_url(provider),
            {"redirect_uri": "https://app.example.com/callback"},
        )
        self.assertEqual(response.status_code, 200)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_authorize_response_contains_authorization_url(self, _dec):
        provider = make_provider(name="URL Provider")
        response = self.client.get(
            self._authorize_url(provider),
            {"redirect_uri": "https://app.example.com/callback"},
        )
        self.assertIn("authorization_url", response.data["data"])

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_authorize_response_contains_state_token(self, _dec):
        provider = make_provider(name="State Provider")
        response = self.client.get(
            self._authorize_url(provider),
            {"redirect_uri": "https://app.example.com/callback"},
        )
        self.assertIn("state", response.data["data"])
        self.assertTrue(len(response.data["data"]["state"]) > 0)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_authorize_url_contains_provider_auth_endpoint(self, _dec):
        provider = make_provider(name="Auth Endpoint Provider")
        response = self.client.get(
            self._authorize_url(provider),
            {"redirect_uri": "https://app.example.com/callback"},
        )
        auth_url = response.data["data"]["authorization_url"]
        self.assertIn("https://idp.example.com/auth", auth_url)

    def test_authorize_without_redirect_uri_returns_error(self):
        provider = make_provider(name="No Redirect Provider")
        response = self.client.get(self._authorize_url(provider))
        self.assertIn(response.status_code, [400, 422])

    def test_authorize_with_unknown_provider_code_returns_404(self):
        response = self.client.get(
            "/api/v1/auth/oauth/OAUTH-99999/authorize/",
            {"redirect_uri": "https://app.example.com/callback"},
        )
        self.assertEqual(response.status_code, 404)

    def test_authorize_with_inactive_provider_returns_404(self):
        provider = make_provider(name="Inactive Provider", is_active=False)
        response = self.client.get(
            self._authorize_url(provider),
            {"redirect_uri": "https://app.example.com/callback"},
        )
        self.assertEqual(response.status_code, 404)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_authorize_saves_state_to_session(self, _dec):
        provider = make_provider(name="Session State Provider")
        self.client.get(
            self._authorize_url(provider),
            {"redirect_uri": "https://app.example.com/callback"},
        )
        self.assertIn("oauth_state", self.client.session)
        self.assertIn("oauth_provider_code", self.client.session)
        self.assertIn("oauth_redirect_uri", self.client.session)


class OAuthCallbackAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _seed_session(self, provider, state, redirect_uri="https://app.example.com/cb"):
        session = self.client.session
        session["oauth_state"] = state
        session["oauth_provider_code"] = provider.code
        session["oauth_redirect_uri"] = redirect_uri
        session.save()

    def test_callback_without_code_returns_error(self):
        response = self.client.post(CALLBACK_URL, {"state": "s"}, format="json")
        self.assertIn(response.status_code, [400, 422])

    def test_callback_without_state_returns_error(self):
        response = self.client.post(CALLBACK_URL, {"code": "c"}, format="json")
        self.assertIn(response.status_code, [400, 422])

    def test_callback_with_empty_body_returns_error(self):
        response = self.client.post(CALLBACK_URL, {}, format="json")
        self.assertIn(response.status_code, [400, 422])

    def test_callback_with_mismatched_state_returns_error(self):
        provider = make_provider(name="State Mismatch Provider")
        self._seed_session(provider, state="correct-state")
        response = self.client.post(
            CALLBACK_URL,
            {"code": "auth-code", "state": "wrong-state"},
            format="json",
        )
        self.assertIn(response.status_code, [400, 422])

    def test_callback_with_no_session_state_returns_error(self):
        response = self.client.post(
            CALLBACK_URL,
            {"code": "auth-code", "state": "some-state"},
            format="json",
        )
        self.assertIn(response.status_code, [400, 422])

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        return_value={"email": "user@example.com", "sub": "uid-1"},
    )
    @patch(
        "apps.oauth.services.exchange_code", return_value={"access_token": "tok-xyz"}
    )
    def test_callback_with_valid_state_returns_200(self, _exc, _fetch, _dec):
        provider = make_provider(name="Valid Callback Provider")
        self._seed_session(provider, state="valid-state")
        response = self.client.post(
            CALLBACK_URL,
            {"code": "auth-code", "state": "valid-state"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        return_value={"email": "user@example.com", "sub": "uid-1"},
    )
    @patch(
        "apps.oauth.services.exchange_code", return_value={"access_token": "tok-xyz"}
    )
    def test_callback_response_contains_user_email(self, _exc, _fetch, _dec):
        provider = make_provider(name="User Email Provider")
        self._seed_session(provider, state="state-abc")
        response = self.client.post(
            CALLBACK_URL,
            {"code": "auth-code", "state": "state-abc"},
            format="json",
        )
        self.assertEqual(response.data["data"]["user"]["email"], "user@example.com")

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        return_value={"email": "user@example.com", "sub": "uid-1"},
    )
    @patch(
        "apps.oauth.services.exchange_code", return_value={"access_token": "tok-xyz"}
    )
    def test_callback_response_user_has_expected_fields(self, _exc, _fetch, _dec):
        provider = make_provider(name="User Fields Provider")
        self._seed_session(provider, state="state-fields")
        response = self.client.post(
            CALLBACK_URL,
            {"code": "auth-code", "state": "state-fields"},
            format="json",
        )
        user_data = response.data["data"]["user"]
        for field in ["id", "email", "first_name", "last_name", "is_superuser"]:
            self.assertIn(field, user_data)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        return_value={"email": "session@example.com", "sub": "uid-sess"},
    )
    @patch(
        "apps.oauth.services.exchange_code", return_value={"access_token": "tok-xyz"}
    )
    def test_callback_clears_oauth_session_keys_after_success(self, _exc, _fetch, _dec):
        provider = make_provider(name="Session Clear Provider")
        self._seed_session(provider, state="clear-state")
        self.client.post(
            CALLBACK_URL,
            {"code": "auth-code", "state": "clear-state"},
            format="json",
        )
        session = self.client.session
        self.assertNotIn("oauth_state", session)
        self.assertNotIn("oauth_provider_code", session)
        self.assertNotIn("oauth_redirect_uri", session)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch("apps.oauth.services.exchange_code", side_effect=Exception("network error"))
    def test_callback_returns_503_on_token_exchange_failure(self, _exc, _dec):
        provider = make_provider(name="Network Fail Provider")
        self._seed_session(provider, state="fail-state")
        response = self.client.post(
            CALLBACK_URL,
            {"code": "auth-code", "state": "fail-state"},
            format="json",
        )
        self.assertEqual(response.status_code, 503)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        return_value={"sub": "uid-no-email"},
    )
    @patch(
        "apps.oauth.services.exchange_code", return_value={"access_token": "tok-abc"}
    )
    def test_callback_returns_error_when_provider_sends_no_email(
        self, _exc, _fetch, _dec
    ):
        provider = make_provider(name="No Email IdP")
        self._seed_session(provider, state="no-email-state")
        response = self.client.post(
            CALLBACK_URL,
            {"code": "auth-code", "state": "no-email-state"},
            format="json",
        )
        self.assertIn(response.status_code, [400, 422])
