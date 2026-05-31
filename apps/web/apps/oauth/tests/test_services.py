import urllib.error
from unittest.mock import patch

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    ServiceUnavailableException,
    ValidationException,
)
from apps.oauth.models import OAuth
from apps.oauth.services import AdminOAuthService, OAuthFlowService, OAuthService
from apps.users.models import User

PROVIDER_DEFAULTS = {
    "name": "Test IdP",
    "client_id": "my-client-id",
    "client_secret": "my-client-secret",
    "auth_endpoint": "https://idp.example.com/auth",
    "token_endpoint": "https://idp.example.com/token",
    "userinfo_endpoint": "https://idp.example.com/userinfo",
    "scope": "openid email profile",
}

PROVIDER_BASE = {
    "client_id": "raw-cid",
    "client_secret": "raw-secret",
    "auth_endpoint": "https://idp.example.com/auth",
    "token_endpoint": "https://idp.example.com/token",
    "userinfo_endpoint": "https://idp.example.com/userinfo",
    "scope": "openid email",
}


def make_provider(name="Flow Provider", **overrides):
    return OAuth.objects.create(name=name, **{**PROVIDER_BASE, **overrides})


class OAuthServiceCreateTest(TestCase):
    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_returns_oauth_instance(self, _prefix, _enc):
        svc = OAuthService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertIsInstance(provider, OAuth)

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_stores_provider_name(self, _prefix, _enc):
        svc = OAuthService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertEqual(provider.name, "Test IdP")

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_generates_oauth_code(self, _prefix, _enc):
        svc = OAuthService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertTrue(provider.code.startswith("OAUTH-"))

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_sets_is_active_true(self, _prefix, _enc):
        svc = OAuthService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertTrue(provider.is_active)

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_sets_created_by_from_user(self, _prefix, _enc):
        user = User.objects.create_user(
            username="admin@example.com", email="admin@example.com", password="pass"
        )
        svc = OAuthService(user=user)
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertEqual(provider.created_by, user)

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_raises_already_exists_for_duplicate_name(self, _prefix, _enc):
        svc = OAuthService()
        svc.create(**PROVIDER_DEFAULTS)
        with self.assertRaises(AlreadyExistsException):
            svc.create(**PROVIDER_DEFAULTS)

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_create_persists_provider_to_database(self, _prefix, _enc):
        svc = OAuthService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertTrue(OAuth.objects.filter(pk=provider.pk).exists())


class AdminOAuthServiceCreateTest(TestCase):
    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_admin_create_succeeds_without_user(self, _prefix, _enc):
        svc = AdminOAuthService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertIsInstance(provider, OAuth)

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_admin_create_sets_created_by_to_none(self, _prefix, _enc):
        svc = AdminOAuthService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertIsNone(provider.created_by)

    @patch("apps.oauth.services.encrypt_value", side_effect=lambda v, _: v)
    @patch("apps.oauth.services.Infra.get_secrets_prefix", return_value="")
    def test_admin_create_raises_already_exists_for_duplicate_name(self, _prefix, _enc):
        svc = AdminOAuthService()
        svc.create(**PROVIDER_DEFAULTS)
        with self.assertRaises(AlreadyExistsException):
            svc.create(**PROVIDER_DEFAULTS)


class OAuthFlowServiceBuildAuthorizeUrlTest(TestCase):
    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_url_starts_with_auth_endpoint(self, _dec):
        provider = make_provider()
        svc = OAuthFlowService()
        url = svc.build_authorize_url(
            provider=provider,
            redirect_uri="https://app.example.com/callback",
            state="state-token-xyz",
        )
        self.assertTrue(url.startswith("https://idp.example.com/auth"))

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_url_contains_response_type_code(self, _dec):
        provider = make_provider()
        svc = OAuthFlowService()
        url = svc.build_authorize_url(
            provider=provider,
            redirect_uri="https://app.example.com/callback",
            state="state-xyz",
        )
        self.assertIn("response_type=code", url)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_url_contains_state_param(self, _dec):
        provider = make_provider()
        svc = OAuthFlowService()
        url = svc.build_authorize_url(
            provider=provider,
            redirect_uri="https://app.example.com/callback",
            state="my-unique-state",
        )
        self.assertIn("my-unique-state", url)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_url_contains_scope(self, _dec):
        provider = make_provider(scope="openid email profile")
        svc = OAuthFlowService()
        url = svc.build_authorize_url(
            provider=provider,
            redirect_uri="https://app.example.com/callback",
            state="s",
        )
        self.assertIn("scope=", url)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    def test_url_contains_redirect_uri(self, _dec):
        provider = make_provider()
        svc = OAuthFlowService()
        url = svc.build_authorize_url(
            provider=provider,
            redirect_uri="https://app.example.com/callback",
            state="s",
        )
        self.assertIn("redirect_uri=", url)


class OAuthFlowServiceCompleteLoginTest(TestCase):
    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        return_value={"email": "user@example.com", "sub": "uid-1"},
    )
    @patch(
        "apps.oauth.services.exchange_code", return_value={"access_token": "tok-abc"}
    )
    def test_creates_new_user_on_first_login(self, _exc, _fetch, _dec):
        provider = make_provider(name="Login Provider")
        svc = OAuthFlowService()
        user = svc.complete_login(
            provider=provider,
            code="auth-code",
            redirect_uri="https://app.example.com/cb",
        )
        self.assertEqual(user.email, "user@example.com")

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        return_value={"email": "returning@example.com", "sub": "uid-ret"},
    )
    @patch(
        "apps.oauth.services.exchange_code", return_value={"access_token": "tok-abc"}
    )
    def test_returns_same_user_on_repeat_login(self, _exc, _fetch, _dec):
        provider = make_provider(name="Repeat Login Provider")
        svc = OAuthFlowService()
        user1 = svc.complete_login(
            provider=provider, code="code1", redirect_uri="https://app.example.com/cb"
        )
        user2 = svc.complete_login(
            provider=provider, code="code2", redirect_uri="https://app.example.com/cb"
        )
        self.assertEqual(user1.pk, user2.pk)

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.exchange_code", side_effect=Exception("connection refused")
    )
    def test_raises_service_unavailable_on_exchange_error(self, _exc, _dec):
        provider = make_provider(name="Network Error Provider")
        svc = OAuthFlowService()
        with self.assertRaises(ServiceUnavailableException):
            svc.complete_login(
                provider=provider,
                code="bad-code",
                redirect_uri="https://app.example.com/cb",
            )

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch("apps.oauth.services.exchange_code", return_value={})
    def test_raises_service_unavailable_when_no_access_token(self, _exc, _dec):
        provider = make_provider(name="No Token Provider")
        svc = OAuthFlowService()
        with self.assertRaises(ServiceUnavailableException):
            svc.complete_login(
                provider=provider,
                code="code",
                redirect_uri="https://app.example.com/cb",
            )

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        side_effect=Exception("userinfo fetch failed"),
    )
    @patch(
        "apps.oauth.services.exchange_code", return_value={"access_token": "tok-abc"}
    )
    def test_raises_service_unavailable_on_userinfo_fetch_error(
        self, _exc, _fetch, _dec
    ):
        provider = make_provider(name="Userinfo Error Provider")
        svc = OAuthFlowService()
        with self.assertRaises(ServiceUnavailableException):
            svc.complete_login(
                provider=provider,
                code="code",
                redirect_uri="https://app.example.com/cb",
            )

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        return_value={"sub": "uid-no-email"},
    )
    @patch(
        "apps.oauth.services.exchange_code", return_value={"access_token": "tok-abc"}
    )
    def test_raises_validation_error_when_provider_returns_no_email(
        self, _exc, _fetch, _dec
    ):
        provider = make_provider(name="No Email Provider")
        svc = OAuthFlowService()
        with self.assertRaises(ValidationException):
            svc.complete_login(
                provider=provider,
                code="code",
                redirect_uri="https://app.example.com/cb",
            )

    @patch("apps.oauth.services.decrypt_value", side_effect=lambda v: v)
    @patch(
        "apps.oauth.services.fetch_userinfo",
        return_value={"email": "user@example.com", "sub": "uid-http"},
    )
    @patch(
        "apps.oauth.services.exchange_code",
        side_effect=urllib.error.HTTPError(
            url="https://idp.example.com/token",
            code=401,
            msg="Unauthorized",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        ),
    )
    def test_raises_service_unavailable_on_http_error_from_token_endpoint(
        self, _exc, _fetch, _dec
    ):
        provider = make_provider(name="HTTP Error Provider")
        svc = OAuthFlowService()
        with self.assertRaises(ServiceUnavailableException):
            svc.complete_login(
                provider=provider,
                code="code",
                redirect_uri="https://app.example.com/cb",
            )
