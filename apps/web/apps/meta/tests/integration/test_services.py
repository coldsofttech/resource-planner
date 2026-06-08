from django.test import TestCase

from apps.configurations.models import Configuration
from apps.meta.services import MetaService
from apps.users.tests.factories import make_superuser, make_user


class _AnonymousUser:
    is_authenticated = False


# ---------------------------------------------------------------------------
# MetaService.get_meta — unauthenticated
# ---------------------------------------------------------------------------


class MetaServiceUnauthenticatedTest(TestCase):
    def test_returns_dict(self):
        self.assertIsInstance(MetaService.get_meta(_AnonymousUser()), dict)

    def test_contains_setup_complete_key(self):
        self.assertIn("setup_complete", MetaService.get_meta(_AnonymousUser()))

    def test_contains_app_name_key(self):
        self.assertIn("app_name", MetaService.get_meta(_AnonymousUser()))

    def test_contains_auth_mode_key(self):
        self.assertIn("auth_mode", MetaService.get_meta(_AnonymousUser()))

    def test_contains_allow_registration_key(self):
        self.assertIn("allow_registration", MetaService.get_meta(_AnonymousUser()))

    def test_contains_oauth_provider_key(self):
        self.assertIn("oauth_provider", MetaService.get_meta(_AnonymousUser()))

    def test_contains_saml_provider_key(self):
        self.assertIn("saml_provider", MetaService.get_meta(_AnonymousUser()))

    def test_does_not_contain_user_key_for_anonymous(self):
        self.assertNotIn("user", MetaService.get_meta(_AnonymousUser()))

    def test_app_name_reflects_configuration(self):
        Configuration.objects.filter(config_code="APP_NAME").update(value="TestApp")
        self.assertEqual(MetaService.get_meta(_AnonymousUser())["app_name"], "TestApp")

    def test_setup_complete_is_false_by_default(self):
        self.assertFalse(MetaService.get_meta(_AnonymousUser())["setup_complete"])


# ---------------------------------------------------------------------------
# MetaService.get_meta — authenticated
# ---------------------------------------------------------------------------


class MetaServiceAuthenticatedTest(TestCase):
    def setUp(self):
        self.user = make_user(first_name="Jane", last_name="Doe")

    def test_contains_user_key_for_authenticated_user(self):
        self.assertIn("user", MetaService.get_meta(self.user))

    def test_user_email_is_correct(self):
        self.assertEqual(
            MetaService.get_meta(self.user)["user"]["email"], "user@example.com"
        )

    def test_user_name_is_full_name(self):
        self.assertEqual(MetaService.get_meta(self.user)["user"]["name"], "Jane Doe")

    def test_user_is_superuser_is_false_for_regular_user(self):
        self.assertFalse(MetaService.get_meta(self.user)["user"]["is_superuser"])

    def test_user_is_superuser_is_true_for_superuser(self):
        admin = make_superuser("admin@example.com")
        self.assertTrue(MetaService.get_meta(admin)["user"]["is_superuser"])

    def test_public_fields_still_present_for_authenticated(self):
        result = MetaService.get_meta(self.user)
        for key in ("setup_complete", "app_name", "auth_mode", "allow_registration"):
            self.assertIn(key, result)
