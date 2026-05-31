from django.test import TestCase

from apps.oauth.models import OAuth
from apps.oauth.selectors import get_active_provider_by_code, provider_exists

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


class ProviderExistsTest(TestCase):
    def test_returns_true_when_provider_exists(self):
        make_provider(name="Existing Provider")
        self.assertTrue(provider_exists("Existing Provider"))

    def test_returns_false_when_provider_does_not_exist(self):
        self.assertFalse(provider_exists("Nonexistent Provider"))

    def test_name_match_is_exact(self):
        make_provider(name="My Provider")
        self.assertFalse(provider_exists("my provider"))
        self.assertFalse(provider_exists("My Provider "))


class GetActiveProviderByCodeTest(TestCase):
    def test_returns_provider_for_active_code(self):
        provider = make_provider(name="Active Provider")
        result = get_active_provider_by_code(provider.code)
        self.assertEqual(result, provider)

    def test_returns_none_for_inactive_provider(self):
        provider = make_provider(name="Inactive Provider", is_active=False)
        result = get_active_provider_by_code(provider.code)
        self.assertIsNone(result)

    def test_returns_none_for_unknown_code(self):
        result = get_active_provider_by_code("OAUTH-99999")
        self.assertIsNone(result)

    def test_returns_none_for_empty_code(self):
        result = get_active_provider_by_code("")
        self.assertIsNone(result)

    def test_does_not_return_other_providers(self):
        p1 = make_provider(name="Provider One")
        make_provider(name="Provider Two")
        result = get_active_provider_by_code(p1.code)
        self.assertEqual(result.name, "Provider One")
