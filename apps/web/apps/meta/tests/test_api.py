from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.models import User

META_URL = "/api/v1/meta/"

PUBLIC_META = {
    "app_name": "TestApp",
    "auth_mode": "classic",
    "allow_registration": True,
}

USER_META = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "is_superuser": False,
}


class MetaUnauthenticatedTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_returns_200(self, _pub):
        response = self.client.get(META_URL)
        self.assertEqual(response.status_code, 200)

    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_response_success_flag_is_true(self, _pub):
        response = self.client.get(META_URL)
        self.assertTrue(response.data["success"])

    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_response_message(self, _pub):
        response = self.client.get(META_URL)
        self.assertEqual(response.data["message"], "Meta fetched.")

    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_response_contains_app_name(self, _pub):
        response = self.client.get(META_URL)
        self.assertEqual(response.data["data"]["app_name"], "TestApp")

    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_response_contains_auth_mode(self, _pub):
        response = self.client.get(META_URL)
        self.assertEqual(response.data["data"]["auth_mode"], "classic")

    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_response_contains_allow_registration(self, _pub):
        response = self.client.get(META_URL)
        self.assertIn("allow_registration", response.data["data"])

    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_does_not_include_user_when_unauthenticated(self, _pub):
        response = self.client.get(META_URL)
        self.assertNotIn("user", response.data["data"])


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

    @patch("apps.meta.services.get_user_meta", return_value=USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_returns_200_when_authenticated(self, _pub, _usr):
        response = self.client.get(META_URL)
        self.assertEqual(response.status_code, 200)

    @patch("apps.meta.services.get_user_meta", return_value=USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_includes_user_when_authenticated(self, _pub, _usr):
        response = self.client.get(META_URL)
        self.assertIn("user", response.data["data"])

    @patch("apps.meta.services.get_user_meta", return_value=USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_user_contains_name(self, _pub, _usr):
        response = self.client.get(META_URL)
        self.assertEqual(response.data["data"]["user"]["name"], "Jane Doe")

    @patch("apps.meta.services.get_user_meta", return_value=USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_user_contains_email(self, _pub, _usr):
        response = self.client.get(META_URL)
        self.assertEqual(response.data["data"]["user"]["email"], "jane@example.com")

    @patch("apps.meta.services.get_user_meta", return_value=USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_user_contains_is_superuser(self, _pub, _usr):
        response = self.client.get(META_URL)
        self.assertIn("is_superuser", response.data["data"]["user"])

    @patch("apps.meta.services.get_user_meta", return_value=USER_META)
    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_does_not_expose_password_in_user(self, _pub, _usr):
        response = self.client.get(META_URL)
        self.assertNotIn("password", response.data["data"].get("user", {}))

    @patch(
        "apps.meta.services.get_user_meta",
        return_value={**USER_META, "is_superuser": True},
    )
    @patch("apps.meta.services.get_public_meta", return_value=PUBLIC_META)
    def test_meta_reflects_superuser_flag(self, _pub, _usr):
        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(META_URL)
        self.assertTrue(response.data["data"]["user"]["is_superuser"])
