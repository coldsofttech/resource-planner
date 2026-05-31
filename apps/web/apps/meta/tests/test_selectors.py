from django.test import TestCase

from apps.configurations.models import Configuration
from apps.meta.selectors import get_public_meta, get_user_meta
from apps.users.models import User


def make_user(
    email="user@example.com",
    first_name="Jane",
    last_name="Doe",
    is_superuser=False,
):
    if is_superuser:
        return User.objects.create_superuser(
            username=email,
            email=email,
            password="pass",
            first_name=first_name,
            last_name=last_name,
        )
    return User.objects.create_user(
        username=email,
        email=email,
        password="pass",
        first_name=first_name,
        last_name=last_name,
    )


# ---------------------------------------------------------------------------
# get_public_meta
# ---------------------------------------------------------------------------


class GetPublicMetaTest(TestCase):
    def test_returns_setup_complete_key(self):
        meta = get_public_meta()
        self.assertIn("setup_complete", meta)

    def test_returns_app_name_key(self):
        meta = get_public_meta()
        self.assertIn("app_name", meta)

    def test_returns_auth_mode_key(self):
        meta = get_public_meta()
        self.assertIn("auth_mode", meta)

    def test_returns_allow_registration_key(self):
        meta = get_public_meta()
        self.assertIn("allow_registration", meta)

    def test_setup_complete_is_false_by_default(self):
        meta = get_public_meta()
        self.assertFalse(meta["setup_complete"])

    def test_setup_complete_is_true_when_set(self):
        Configuration.objects.filter(config_code="SETUP_COMPLETE").update(value="true")
        meta = get_public_meta()
        self.assertTrue(meta["setup_complete"])

    def test_app_name_reflects_configured_value(self):
        Configuration.objects.filter(config_code="APP_NAME").update(value="MyTestApp")
        meta = get_public_meta()
        self.assertEqual(meta["app_name"], "MyTestApp")

    def test_auth_mode_reflects_configured_value(self):
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="classic")
        meta = get_public_meta()
        self.assertEqual(meta["auth_mode"], "classic")

    def test_allow_registration_is_true_by_default(self):
        meta = get_public_meta()
        self.assertTrue(meta["allow_registration"])

    def test_allow_registration_is_false_when_disabled(self):
        Configuration.objects.filter(config_code="ALLOW_REGISTRATION").update(
            value="false"
        )
        meta = get_public_meta()
        self.assertFalse(meta["allow_registration"])

    def test_auth_mode_value_is_string(self):
        meta = get_public_meta()
        self.assertIsInstance(meta["auth_mode"], str)


# ---------------------------------------------------------------------------
# get_user_meta
# ---------------------------------------------------------------------------


class GetUserMetaTest(TestCase):
    def test_returns_name_key(self):
        user = make_user()
        meta = get_user_meta(user)
        self.assertIn("name", meta)

    def test_returns_email_key(self):
        user = make_user()
        meta = get_user_meta(user)
        self.assertIn("email", meta)

    def test_returns_is_superuser_key(self):
        user = make_user()
        meta = get_user_meta(user)
        self.assertIn("is_superuser", meta)

    def test_full_name_is_concatenated_first_and_last(self):
        user = make_user(first_name="Alice", last_name="Smith")
        meta = get_user_meta(user)
        self.assertEqual(meta["name"], "Alice Smith")

    def test_name_strips_extra_whitespace_for_single_name(self):
        user = make_user(first_name="Alice", last_name="")
        meta = get_user_meta(user)
        self.assertEqual(meta["name"], "Alice")

    def test_name_falls_back_to_username_when_no_names_set(self):
        user = make_user(first_name="", last_name="", email="user@example.com")
        meta = get_user_meta(user)
        self.assertEqual(meta["name"], user.username)

    def test_email_is_correct(self):
        user = make_user(email="jane@example.com")
        meta = get_user_meta(user)
        self.assertEqual(meta["email"], "jane@example.com")

    def test_is_superuser_is_false_for_regular_user(self):
        user = make_user()
        meta = get_user_meta(user)
        self.assertFalse(meta["is_superuser"])

    def test_is_superuser_is_true_for_superuser(self):
        user = make_user(is_superuser=True)
        meta = get_user_meta(user)
        self.assertTrue(meta["is_superuser"])


# ---------------------------------------------------------------------------
# get_public_meta — OAuth auth mode
# ---------------------------------------------------------------------------

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


class GetPublicMetaOAuthModeTest(TestCase):
    def setUp(self):
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="oauth")

    def test_oauth_provider_populated_when_active_provider_exists(self):
        from apps.oauth.models import OAuth

        provider = OAuth.objects.create(
            name="Active OAuth Provider", is_active=True, **_OAUTH_BASE
        )
        meta = get_public_meta()
        self.assertIsNotNone(meta["oauth_provider"])
        self.assertEqual(meta["oauth_provider"]["code"], provider.code)

    def test_oauth_provider_is_none_when_no_active_provider(self):
        meta = get_public_meta()
        self.assertIsNone(meta["oauth_provider"])

    def test_saml_provider_is_none_in_oauth_mode(self):
        meta = get_public_meta()
        self.assertIsNone(meta["saml_provider"])

    def test_oauth_provider_dict_contains_code_name_icon(self):
        from apps.oauth.models import OAuth

        OAuth.objects.create(name="Dict OAuth Provider", is_active=True, **_OAUTH_BASE)
        meta = get_public_meta()
        provider_dict = meta["oauth_provider"]
        for key in ["code", "name", "icon"]:
            self.assertIn(key, provider_dict)

    def test_oauth_provider_name_matches_stored_name(self):
        from apps.oauth.models import OAuth

        OAuth.objects.create(name="Named OAuth Provider", is_active=True, **_OAUTH_BASE)
        meta = get_public_meta()
        self.assertEqual(meta["oauth_provider"]["name"], "Named OAuth Provider")


# ---------------------------------------------------------------------------
# get_public_meta — SAML auth mode
# ---------------------------------------------------------------------------


class GetPublicMetaSAMLModeTest(TestCase):
    def setUp(self):
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")

    def test_saml_provider_populated_when_active_provider_exists(self):
        from apps.saml.models import SAML

        provider = SAML.objects.create(
            name="Active SAML Provider", is_active=True, **_SAML_BASE
        )
        meta = get_public_meta()
        self.assertIsNotNone(meta["saml_provider"])
        self.assertEqual(meta["saml_provider"]["code"], provider.code)

    def test_saml_provider_is_none_when_no_active_provider(self):
        meta = get_public_meta()
        self.assertIsNone(meta["saml_provider"])

    def test_oauth_provider_is_none_in_saml_mode(self):
        meta = get_public_meta()
        self.assertIsNone(meta["oauth_provider"])

    def test_saml_provider_dict_contains_code_name_icon(self):
        from apps.saml.models import SAML

        SAML.objects.create(name="Dict SAML Provider", is_active=True, **_SAML_BASE)
        meta = get_public_meta()
        provider_dict = meta["saml_provider"]
        for key in ["code", "name", "icon"]:
            self.assertIn(key, provider_dict)

    def test_saml_provider_name_matches_stored_name(self):
        from apps.saml.models import SAML

        SAML.objects.create(name="Named SAML Provider", is_active=True, **_SAML_BASE)
        meta = get_public_meta()
        self.assertEqual(meta["saml_provider"]["name"], "Named SAML Provider")
