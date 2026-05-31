from django.test import TestCase

from apps.configurations.models import Configuration
from apps.meta.services import MetaService
from apps.users.models import User


def make_user(email="user@example.com", first_name="Jane", last_name="Doe"):
    return User.objects.create_user(
        username=email,
        email=email,
        password="pass",
        first_name=first_name,
        last_name=last_name,
    )


class AnonymousUser:
    """Minimal stand-in for an unauthenticated request.user."""

    is_authenticated = False


# ---------------------------------------------------------------------------
# MetaService.get_meta — unauthenticated
# ---------------------------------------------------------------------------


class MetaServiceUnauthenticatedTest(TestCase):
    def test_returns_dict(self):
        result = MetaService.get_meta(AnonymousUser())
        self.assertIsInstance(result, dict)

    def test_contains_setup_complete_key(self):
        result = MetaService.get_meta(AnonymousUser())
        self.assertIn("setup_complete", result)

    def test_contains_app_name_key(self):
        result = MetaService.get_meta(AnonymousUser())
        self.assertIn("app_name", result)

    def test_contains_auth_mode_key(self):
        result = MetaService.get_meta(AnonymousUser())
        self.assertIn("auth_mode", result)

    def test_contains_allow_registration_key(self):
        result = MetaService.get_meta(AnonymousUser())
        self.assertIn("allow_registration", result)

    def test_does_not_contain_user_key_for_anonymous(self):
        result = MetaService.get_meta(AnonymousUser())
        self.assertNotIn("user", result)

    def test_app_name_reflects_configuration(self):
        Configuration.objects.filter(config_code="APP_NAME").update(value="TestApp")
        result = MetaService.get_meta(AnonymousUser())
        self.assertEqual(result["app_name"], "TestApp")

    def test_setup_complete_is_false_by_default(self):
        result = MetaService.get_meta(AnonymousUser())
        self.assertFalse(result["setup_complete"])


# ---------------------------------------------------------------------------
# MetaService.get_meta — authenticated
# ---------------------------------------------------------------------------


class MetaServiceAuthenticatedTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_contains_user_key_for_authenticated_user(self):
        result = MetaService.get_meta(self.user)
        self.assertIn("user", result)

    def test_user_email_is_correct(self):
        result = MetaService.get_meta(self.user)
        self.assertEqual(result["user"]["email"], "user@example.com")

    def test_user_name_is_full_name(self):
        result = MetaService.get_meta(self.user)
        self.assertEqual(result["user"]["name"], "Jane Doe")

    def test_user_is_superuser_is_false_for_regular_user(self):
        result = MetaService.get_meta(self.user)
        self.assertFalse(result["user"]["is_superuser"])

    def test_user_is_superuser_is_true_for_superuser(self):
        admin = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="pass",
        )
        result = MetaService.get_meta(admin)
        self.assertTrue(result["user"]["is_superuser"])

    def test_public_fields_still_present_for_authenticated(self):
        result = MetaService.get_meta(self.user)
        for key in ["setup_complete", "app_name", "auth_mode", "allow_registration"]:
            self.assertIn(key, result)
