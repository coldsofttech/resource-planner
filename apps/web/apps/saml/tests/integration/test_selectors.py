from django.test import TestCase

from apps.saml.selectors import (
    get_active_provider,
    get_active_provider_by_code,
    get_provider_by_entity_id,
    provider_exists,
)
from apps.saml.tests.factories import make_provider


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


class GetActiveProviderTest(TestCase):
    def test_returns_none_when_no_providers_exist(self):
        self.assertIsNone(get_active_provider())

    def test_returns_active_provider(self):
        provider = make_provider(name="Active Provider")
        self.assertEqual(get_active_provider(), provider)

    def test_returns_none_when_all_providers_are_inactive(self):
        make_provider(name="Inactive Provider", is_active=False)
        self.assertIsNone(get_active_provider())

    def test_returns_active_provider_among_mixed(self):
        make_provider(name="Inactive One", is_active=False)
        active = make_provider(name="Active One", is_active=True)
        self.assertEqual(get_active_provider(), active)


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
        result = get_active_provider_by_code("SAML-99999")
        self.assertIsNone(result)

    def test_returns_none_for_empty_code(self):
        result = get_active_provider_by_code("")
        self.assertIsNone(result)

    def test_does_not_return_other_providers(self):
        p1 = make_provider(name="Provider One")
        make_provider(name="Provider Two")
        result = get_active_provider_by_code(p1.code)
        self.assertEqual(result.name, "Provider One")


class GetProviderByEntityIdTest(TestCase):
    def test_returns_provider_for_matching_entity_id(self):
        provider = make_provider(name="Entity Provider")
        result = get_provider_by_entity_id("https://idp.example.com/entity")
        self.assertEqual(result, provider)

    def test_returns_none_for_unknown_entity_id(self):
        result = get_provider_by_entity_id("https://unknown.example.com/entity")
        self.assertIsNone(result)

    def test_returns_none_for_inactive_provider(self):
        make_provider(name="Inactive Entity Provider", is_active=False)
        result = get_provider_by_entity_id("https://idp.example.com/entity")
        self.assertIsNone(result)

    def test_returns_none_for_empty_entity_id(self):
        result = get_provider_by_entity_id("")
        self.assertIsNone(result)

    def test_returns_first_match_when_multiple_active_providers_share_entity_id(self):
        p1 = make_provider(
            name="Provider One",
            idp_entity_id="https://shared.example.com/entity",
        )
        make_provider(
            name="Provider Two",
            idp_entity_id="https://shared.example.com/entity",
        )
        result = get_provider_by_entity_id("https://shared.example.com/entity")
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, p1.pk)
