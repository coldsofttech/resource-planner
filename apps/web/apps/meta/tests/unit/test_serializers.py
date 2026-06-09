from django.test import SimpleTestCase

from apps.meta.serializers import (
    MetaSerializer,
    MetaSSOProviderSerializer,
    MetaUserSerializer,
)

_USER_DATA = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "is_superuser": False,
}

_SSO_PROVIDER = {"code": "google", "name": "Google", "icon": "bi-google"}

_META_PUBLIC = {
    "setup_complete": True,
    "app_name": "Resource Planner",
    "auth_mode": "classic",
    "allow_registration": True,
}

_META_WITH_NULL_PROVIDERS = {
    **_META_PUBLIC,
    "oauth_provider": None,
    "saml_provider": None,
}

_META_WITH_USER = {
    **_META_PUBLIC,
    "user": _USER_DATA,
}

_META_WITH_OAUTH = {
    **_META_WITH_NULL_PROVIDERS,
    "auth_mode": "oauth",
    "oauth_provider": _SSO_PROVIDER,
}

_META_WITH_SAML = {
    **_META_WITH_NULL_PROVIDERS,
    "auth_mode": "saml",
    "saml_provider": _SSO_PROVIDER,
}


# ---------------------------------------------------------------------------
# MetaUserSerializer
# ---------------------------------------------------------------------------


class MetaUserSerializerTest(SimpleTestCase):
    def test_serializes_name_field(self):
        self.assertIn("name", MetaUserSerializer(_USER_DATA).data)

    def test_serializes_email_field(self):
        self.assertIn("email", MetaUserSerializer(_USER_DATA).data)

    def test_serializes_is_superuser_field(self):
        self.assertIn("is_superuser", MetaUserSerializer(_USER_DATA).data)

    def test_name_value_is_correct(self):
        self.assertEqual(MetaUserSerializer(_USER_DATA).data["name"], "Jane Doe")

    def test_email_value_is_correct(self):
        self.assertEqual(
            MetaUserSerializer(_USER_DATA).data["email"], "jane@example.com"
        )

    def test_is_superuser_false_for_regular_user(self):
        self.assertFalse(MetaUserSerializer(_USER_DATA).data["is_superuser"])

    def test_is_superuser_true_for_admin(self):
        data = MetaUserSerializer({**_USER_DATA, "is_superuser": True}).data
        self.assertTrue(data["is_superuser"])


# ---------------------------------------------------------------------------
# MetaSSOProviderSerializer
# ---------------------------------------------------------------------------


class MetaSSOProviderSerializerTest(SimpleTestCase):
    def test_serializes_code_field(self):
        self.assertIn("code", MetaSSOProviderSerializer(_SSO_PROVIDER).data)

    def test_serializes_name_field(self):
        self.assertIn("name", MetaSSOProviderSerializer(_SSO_PROVIDER).data)

    def test_serializes_icon_field(self):
        self.assertIn("icon", MetaSSOProviderSerializer(_SSO_PROVIDER).data)

    def test_code_value_is_correct(self):
        self.assertEqual(
            MetaSSOProviderSerializer(_SSO_PROVIDER).data["code"], "google"
        )

    def test_name_value_is_correct(self):
        self.assertEqual(
            MetaSSOProviderSerializer(_SSO_PROVIDER).data["name"], "Google"
        )

    def test_icon_value_is_correct(self):
        self.assertEqual(
            MetaSSOProviderSerializer(_SSO_PROVIDER).data["icon"], "bi-google"
        )


# ---------------------------------------------------------------------------
# MetaSerializer — public fields (no providers in source dict)
# ---------------------------------------------------------------------------


class MetaSerializerPublicTest(SimpleTestCase):
    def test_serializes_setup_complete_field(self):
        self.assertIn("setup_complete", MetaSerializer(_META_PUBLIC).data)

    def test_serializes_app_name_field(self):
        self.assertIn("app_name", MetaSerializer(_META_PUBLIC).data)

    def test_serializes_auth_mode_field(self):
        self.assertIn("auth_mode", MetaSerializer(_META_PUBLIC).data)

    def test_serializes_allow_registration_field(self):
        self.assertIn("allow_registration", MetaSerializer(_META_PUBLIC).data)

    def test_setup_complete_value_is_correct(self):
        self.assertTrue(MetaSerializer(_META_PUBLIC).data["setup_complete"])

    def test_app_name_value_is_correct(self):
        self.assertEqual(
            MetaSerializer(_META_PUBLIC).data["app_name"], "Resource Planner"
        )

    def test_auth_mode_value_is_correct(self):
        self.assertEqual(MetaSerializer(_META_PUBLIC).data["auth_mode"], "classic")

    def test_allow_registration_value_is_correct(self):
        self.assertTrue(MetaSerializer(_META_PUBLIC).data["allow_registration"])

    def test_user_is_absent_when_not_provided(self):
        self.assertNotIn("user", MetaSerializer(_META_PUBLIC).data)


# ---------------------------------------------------------------------------
# MetaSerializer — null providers (classic mode with all keys present)
# ---------------------------------------------------------------------------


class MetaSerializerNullProvidersTest(SimpleTestCase):
    def test_oauth_provider_is_null(self):
        data = MetaSerializer(_META_WITH_NULL_PROVIDERS).data
        self.assertIsNone(data["oauth_provider"])

    def test_saml_provider_is_null(self):
        data = MetaSerializer(_META_WITH_NULL_PROVIDERS).data
        self.assertIsNone(data["saml_provider"])

    def test_public_fields_still_present(self):
        data = MetaSerializer(_META_WITH_NULL_PROVIDERS).data
        for key in ("setup_complete", "app_name", "auth_mode", "allow_registration"):
            self.assertIn(key, data)


# ---------------------------------------------------------------------------
# MetaSerializer — oauth_provider populated
# ---------------------------------------------------------------------------


class MetaSerializerOAuthProviderTest(SimpleTestCase):
    def test_oauth_provider_is_not_null(self):
        data = MetaSerializer(_META_WITH_OAUTH).data
        self.assertIsNotNone(data["oauth_provider"])

    def test_oauth_provider_contains_code(self):
        data = MetaSerializer(_META_WITH_OAUTH).data
        self.assertEqual(data["oauth_provider"]["code"], "google")

    def test_oauth_provider_contains_name(self):
        data = MetaSerializer(_META_WITH_OAUTH).data
        self.assertEqual(data["oauth_provider"]["name"], "Google")

    def test_oauth_provider_contains_icon(self):
        data = MetaSerializer(_META_WITH_OAUTH).data
        self.assertEqual(data["oauth_provider"]["icon"], "bi-google")

    def test_saml_provider_is_null_in_oauth_mode(self):
        data = MetaSerializer(_META_WITH_OAUTH).data
        self.assertIsNone(data["saml_provider"])


# ---------------------------------------------------------------------------
# MetaSerializer — saml_provider populated
# ---------------------------------------------------------------------------


class MetaSerializerSAMLProviderTest(SimpleTestCase):
    def test_saml_provider_is_not_null(self):
        data = MetaSerializer(_META_WITH_SAML).data
        self.assertIsNotNone(data["saml_provider"])

    def test_saml_provider_contains_code(self):
        data = MetaSerializer(_META_WITH_SAML).data
        self.assertEqual(data["saml_provider"]["code"], "google")

    def test_saml_provider_contains_name(self):
        data = MetaSerializer(_META_WITH_SAML).data
        self.assertEqual(data["saml_provider"]["name"], "Google")

    def test_saml_provider_contains_icon(self):
        data = MetaSerializer(_META_WITH_SAML).data
        self.assertEqual(data["saml_provider"]["icon"], "bi-google")

    def test_oauth_provider_is_null_in_saml_mode(self):
        data = MetaSerializer(_META_WITH_SAML).data
        self.assertIsNone(data["oauth_provider"])


# ---------------------------------------------------------------------------
# MetaSerializer — authenticated (user present)
# ---------------------------------------------------------------------------


class MetaSerializerAuthenticatedTest(SimpleTestCase):
    def test_user_is_present_when_provided(self):
        self.assertIn("user", MetaSerializer(_META_WITH_USER).data)

    def test_user_name_is_correct(self):
        self.assertEqual(
            MetaSerializer(_META_WITH_USER).data["user"]["name"], "Jane Doe"
        )

    def test_user_email_is_correct(self):
        self.assertEqual(
            MetaSerializer(_META_WITH_USER).data["user"]["email"], "jane@example.com"
        )

    def test_user_is_superuser_is_correct(self):
        self.assertFalse(MetaSerializer(_META_WITH_USER).data["user"]["is_superuser"])
