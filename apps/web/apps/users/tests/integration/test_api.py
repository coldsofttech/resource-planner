from django.test import TestCase
from rest_framework.test import APIClient

from apps.auth.services import UserTokenService
from apps.configurations.tests.factories import mark_setup_complete
from apps.users.tests.factories import make_profile, make_user

USERS_ME_URL = "/api/v1/users/me/preferences/"


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/me/preferences/ — unauthenticated
# ---------------------------------------------------------------------------


class UsersMePatchUnauthenticatedTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(USERS_ME_URL, {"theme": "dark"}, format="json")
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/me/preferences/ — authenticated
# ---------------------------------------------------------------------------


class UsersMePatchAuthenticatedTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(email="prefs@example.com")
        make_profile(user=self.user, theme="light")
        token = UserTokenService(user=self.user, request=None).create_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_valid_theme_returns_200(self):
        response = self.client.patch(USERS_ME_URL, {"theme": "dark"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_response_success_is_true(self):
        response = self.client.patch(USERS_ME_URL, {"theme": "dark"}, format="json")
        self.assertTrue(response.data["success"])

    def test_theme_persisted_to_database(self):
        self.client.patch(USERS_ME_URL, {"theme": "system"}, format="json")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.theme, "system")

    def test_invalid_theme_returns_400(self):
        response = self.client.patch(USERS_ME_URL, {"theme": "purple"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_theme_returns_400(self):
        response = self.client.patch(USERS_ME_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)
