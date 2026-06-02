from unittest.mock import patch

from django.test import TestCase

from apps.users.models import User

_SETUP_COMPLETE = "apps.configurations.selectors.Setup.is_setup_complete"


# ---------------------------------------------------------------------------
# GET /login/ — LoginView
# ---------------------------------------------------------------------------


class LoginViewTest(TestCase):
    def test_get_returns_200(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)

    def test_get_renders_login_template(self):
        response = self.client.get("/login/")
        self.assertTemplateUsed(response, "auth/login.html")

    def test_get_sets_csrf_cookie(self):
        response = self.client.get("/login/")
        self.assertIn("csrftoken", response.cookies)

    def test_post_is_not_handled_by_view(self):
        response = self.client.post("/login/", {})
        self.assertEqual(response.status_code, 405)

    def test_authenticated_user_is_redirected_to_dashboard(self):
        user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)
        response = self.client.get("/login/")
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# GET /forgot-password/ — ForgotPasswordView
# ---------------------------------------------------------------------------


class ForgotPasswordViewTest(TestCase):
    def test_get_returns_200(self):
        response = self.client.get("/forgot-password/")
        self.assertEqual(response.status_code, 200)

    def test_get_renders_forgot_password_template(self):
        response = self.client.get("/forgot-password/")
        self.assertTemplateUsed(response, "auth/forgot_password.html")

    def test_get_sets_csrf_cookie(self):
        response = self.client.get("/forgot-password/")
        self.assertIn("csrftoken", response.cookies)

    def test_post_is_not_handled_by_view(self):
        response = self.client.post("/forgot-password/", {})
        self.assertEqual(response.status_code, 405)

    def test_authenticated_user_is_redirected_to_dashboard(self):
        user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)
        response = self.client.get("/forgot-password/")
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# GET /register/ — RegisterView
# ---------------------------------------------------------------------------


class RegisterViewTest(TestCase):
    def test_get_returns_200(self):
        response = self.client.get("/register/")
        self.assertEqual(response.status_code, 200)

    def test_get_renders_register_template(self):
        response = self.client.get("/register/")
        self.assertTemplateUsed(response, "auth/register.html")

    def test_get_sets_csrf_cookie(self):
        response = self.client.get("/register/")
        self.assertIn("csrftoken", response.cookies)

    def test_post_is_not_handled_by_view(self):
        response = self.client.post("/register/", {})
        self.assertEqual(response.status_code, 405)

    def test_authenticated_user_is_redirected_to_dashboard(self):
        user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)
        response = self.client.get("/register/")
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# GET / — root redirect
# SetupMiddleware intercepts "/" when setup is not complete; mock it out so
# the redirect defined in urls.py is what is actually tested here.
# ---------------------------------------------------------------------------


class AuthRootRedirectTest(TestCase):
    def test_root_redirects_to_login(self):
        with patch(_SETUP_COMPLETE, return_value=True):
            response = self.client.get("/")
        self.assertRedirects(
            response,
            "/login/",
            fetch_redirect_response=False,
        )

    def test_root_redirect_is_not_permanent(self):
        with patch(_SETUP_COMPLETE, return_value=True):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_redirected_to_dashboard_from_root(self):
        user = User.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)
        with patch(_SETUP_COMPLETE, return_value=True):
            response = self.client.get("/")
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)
