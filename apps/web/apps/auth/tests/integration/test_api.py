from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.auth.services import UserTokenService
from apps.auth.tests.factories import make_token
from apps.users.models import User
from apps.users.tests.factories import make_profile, make_superuser, make_user

LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"
FP_REQUEST_URL = "/api/v1/auth/forgot-password/"
FP_VERIFY_URL = "/api/v1/auth/forgot-password/verify/"
FP_RESET_URL = "/api/v1/auth/forgot-password/reset/"
REGISTER_URL = "/api/v1/auth/register/"
ME_URL = "/api/v1/auth/me/"

VALID_CREDENTIALS = {
    "email": "user@example.com",
    "password": "StrongPass123!",
}


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login/ — success
# ---------------------------------------------------------------------------


class AuthLoginSuccessTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def test_valid_credentials_return_200(self):
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertEqual(response.status_code, 200)

    def test_response_success_flag_is_true(self):
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertTrue(response.data["success"])

    def test_response_message_is_sign_in_successful(self):
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertEqual(response.data["message"], "Sign in successful.")

    def test_response_data_contains_redirect(self):
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertIn("redirect", response.data["data"])

    def test_redirect_value_is_dashboard(self):
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertEqual(response.data["data"]["redirect"], "/dashboard/")

    def test_session_is_established_after_login(self):
        self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertIn("_auth_user_id", self.client.session)

    def test_response_data_contains_token(self):
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertIn("token", response.data["data"])

    def test_token_is_non_empty_string(self):
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        token = response.data["data"]["token"]
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_token_is_64_characters(self):
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertEqual(len(response.data["data"]["token"]), 64)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login/ — validation errors (400)
# ---------------------------------------------------------------------------


class AuthLoginValidationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_empty_payload_returns_400(self):
        response = self.client.post(LOGIN_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_email_returns_400(self):
        response = self.client.post(LOGIN_URL, {"password": "pass"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_password_returns_400(self):
        response = self.client.post(
            LOGIN_URL, {"email": "user@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_email_format_returns_400(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "not-an-email", "password": "pass"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_string_password_returns_400(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "user@example.com", "password": ""},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_error_response_success_flag_is_false(self):
        response = self.client.post(LOGIN_URL, {}, format="json")
        self.assertFalse(response.data["success"])


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login/ — authentication failures (401 / 403)
# ---------------------------------------------------------------------------


class AuthLoginAuthenticationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def test_wrong_password_returns_401(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "user@example.com", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_nonexistent_email_returns_401(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "nobody@example.com", "password": "SecurePass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_wrong_password_and_nonexistent_email_return_same_status(self):
        r_wrong_pass = self.client.post(
            LOGIN_URL,
            {"email": "user@example.com", "password": "wrongpassword"},
            format="json",
        )
        r_no_user = self.client.post(
            LOGIN_URL,
            {"email": "nobody@example.com", "password": "SecurePass123!"},
            format="json",
        )
        self.assertEqual(r_wrong_pass.status_code, r_no_user.status_code)

    def test_deactivated_user_returns_403(self):
        inactive = make_user(email="inactive@example.com", is_active=False)
        response = self.client.post(
            LOGIN_URL,
            {"email": inactive.email, "password": "SecurePass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_deactivated_user_response_success_flag_is_false(self):
        inactive = make_user(email="inactive@example.com", is_active=False)
        response = self.client.post(
            LOGIN_URL,
            {"email": inactive.email, "password": "SecurePass123!"},
            format="json",
        )
        self.assertFalse(response.data["success"])

    def test_failed_login_does_not_establish_session(self):
        self.client.post(
            LOGIN_URL,
            {"email": "user@example.com", "password": "wrongpassword"},
            format="json",
        )
        self.assertNotIn("_auth_user_id", self.client.session)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login/ — non-classic auth mode
# ---------------------------------------------------------------------------


class AuthLoginNonClassicModeTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_saml_mode_returns_422_for_non_superuser(self):
        from apps.configurations.models import Configuration

        make_user()
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertEqual(response.status_code, 422)

    def test_oauth_mode_returns_422_for_non_superuser(self):
        from apps.configurations.models import Configuration

        make_user()
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="oauth")
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertEqual(response.status_code, 422)

    def test_non_classic_mode_response_success_is_false(self):
        from apps.configurations.models import Configuration

        make_user()
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")
        response = self.client.post(LOGIN_URL, VALID_CREDENTIALS, format="json")
        self.assertFalse(response.data["success"])

    @patch("apps.auth.services.auth_login")
    def test_superuser_can_login_in_saml_mode(self, _mock_login):
        from apps.configurations.models import Configuration

        make_superuser()
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")
        response = self.client.post(
            LOGIN_URL,
            {"email": "admin@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/logout/
# ---------------------------------------------------------------------------


class AuthLogoutTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def test_logout_returns_200(self):
        response = self.client.post(LOGOUT_URL, format="json")
        self.assertEqual(response.status_code, 200)

    def test_logout_success_flag_is_true(self):
        response = self.client.post(LOGOUT_URL, format="json")
        self.assertTrue(response.data["success"])

    def test_logout_message(self):
        response = self.client.post(LOGOUT_URL, format="json")
        self.assertEqual(response.data["message"], "Signed out successfully.")

    def test_logout_without_any_token_succeeds(self):
        response = self.client.post(LOGOUT_URL, format="json")
        self.assertEqual(response.status_code, 200)

    def test_logout_revokes_active_bearer_token(self):
        svc = UserTokenService(user=None, request=None)
        token = svc.create_token(self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
        self.client.post(LOGOUT_URL, format="json")

        token.refresh_from_db()
        self.assertFalse(token.is_active)

    def test_logout_clears_session(self):
        self.client.force_login(self.user)
        self.assertIn("_auth_user_id", self.client.session)
        self.client.post(LOGOUT_URL, format="json")
        self.assertNotIn("_auth_user_id", self.client.session)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/forgot-password/ — request reset
# ---------------------------------------------------------------------------


class ForgotPasswordRequestAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def test_known_email_returns_200(self):
        with patch("apps.auth.services.build_email_sender") as mock_sender:
            mock_sender.return_value.send.return_value = None
            response = self.client.post(
                FP_REQUEST_URL, {"email": self.user.email}, format="json"
            )
        self.assertEqual(response.status_code, 200)

    def test_known_email_response_success_is_true(self):
        with patch("apps.auth.services.build_email_sender") as mock_sender:
            mock_sender.return_value.send.return_value = None
            response = self.client.post(
                FP_REQUEST_URL, {"email": self.user.email}, format="json"
            )
        self.assertTrue(response.data["success"])

    def test_unknown_email_returns_422(self):
        response = self.client.post(
            FP_REQUEST_URL, {"email": "nobody@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, 422)

    def test_inactive_user_returns_422(self):
        make_user(email="inactive@example.com", is_active=False)
        response = self.client.post(
            FP_REQUEST_URL, {"email": "inactive@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, 422)

    def test_missing_email_returns_400(self):
        response = self.client.post(FP_REQUEST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_invalid_email_format_returns_400(self):
        response = self.client.post(
            FP_REQUEST_URL, {"email": "not-an-email"}, format="json"
        )
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/forgot-password/verify/ — verify code
# ---------------------------------------------------------------------------


class ForgotPasswordVerifyAPITest(TestCase):
    def setUp(self):
        from otpcore import hash_otp

        self.client = APIClient()
        self.user = make_user()
        self.valid_code = "654321"
        make_token(self.user, token_hash=hash_otp(self.valid_code))

    def test_valid_code_returns_200(self):
        response = self.client.post(
            FP_VERIFY_URL,
            {"email": self.user.email, "code": self.valid_code},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_valid_code_response_success_is_true(self):
        response = self.client.post(
            FP_VERIFY_URL,
            {"email": self.user.email, "code": self.valid_code},
            format="json",
        )
        self.assertTrue(response.data["success"])

    def test_invalid_code_returns_422(self):
        response = self.client.post(
            FP_VERIFY_URL,
            {"email": self.user.email, "code": "000000"},
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_expired_token_returns_422(self):
        from otpcore import hash_otp

        expired_code = "111111"
        make_token(
            self.user, token_hash=hash_otp(expired_code), minutes_until_expiry=-1
        )
        response = self.client.post(
            FP_VERIFY_URL,
            {"email": self.user.email, "code": expired_code},
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_missing_code_returns_400(self):
        response = self.client.post(
            FP_VERIFY_URL, {"email": self.user.email}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_code_wrong_length_returns_400(self):
        response = self.client.post(
            FP_VERIFY_URL,
            {"email": self.user.email, "code": "12345"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_email_returns_400(self):
        response = self.client.post(
            FP_VERIFY_URL, {"code": self.valid_code}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_email_returns_422(self):
        response = self.client.post(
            FP_VERIFY_URL,
            {"email": "nobody@example.com", "code": self.valid_code},
            format="json",
        )
        self.assertEqual(response.status_code, 422)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/forgot-password/reset/ — reset password
# ---------------------------------------------------------------------------


class ForgotPasswordResetAPITest(TestCase):
    def setUp(self):
        from otpcore import hash_otp

        self.client = APIClient()
        self.user = make_user()
        self.valid_code = "789012"
        make_token(self.user, token_hash=hash_otp(self.valid_code))

    def test_valid_reset_returns_200(self):
        response = self.client.post(
            FP_RESET_URL,
            {
                "email": self.user.email,
                "code": self.valid_code,
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_valid_reset_response_success_is_true(self):
        response = self.client.post(
            FP_RESET_URL,
            {
                "email": self.user.email,
                "code": self.valid_code,
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!",
            },
            format="json",
        )
        self.assertTrue(response.data["success"])

    def test_invalid_code_returns_422(self):
        response = self.client.post(
            FP_RESET_URL,
            {
                "email": self.user.email,
                "code": "000000",
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_mismatched_passwords_returns_error(self):
        response = self.client.post(
            FP_RESET_URL,
            {
                "email": self.user.email,
                "code": self.valid_code,
                "new_password": "NewSecurePass456!",
                "confirm_password": "DifferentPass789!",
            },
            format="json",
        )
        self.assertIn(response.status_code, [400, 422])

    def test_same_as_current_password_returns_422(self):
        response = self.client.post(
            FP_RESET_URL,
            {
                "email": self.user.email,
                "code": self.valid_code,
                "new_password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_missing_fields_returns_400(self):
        response = self.client.post(FP_RESET_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_user_can_login_with_new_password_after_reset(self):
        self.client.post(
            FP_RESET_URL,
            {
                "email": self.user.email,
                "code": self.valid_code,
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!",
            },
            format="json",
        )
        login_response = self.client.post(
            LOGIN_URL,
            {"email": self.user.email, "password": "NewSecurePass456!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register/ — self-registration
# ---------------------------------------------------------------------------

VALID_REGISTER_PAYLOAD = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "password": "SecureRegPass123!",
    "confirm_password": "SecureRegPass123!",
}


class RegisterAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_valid_payload_returns_201(self):
        response = self.client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 201)

    def test_response_success_flag_is_true(self):
        response = self.client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD, format="json")
        self.assertTrue(response.data["success"])

    def test_user_is_created_in_db(self):
        self.client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD, format="json")
        self.assertTrue(User.objects.filter(email="jane@example.com").exists())

    def test_missing_first_name_returns_400(self):
        data = {**VALID_REGISTER_PAYLOAD}
        del data["first_name"]
        response = self.client.post(REGISTER_URL, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_email_returns_400(self):
        data = {**VALID_REGISTER_PAYLOAD}
        del data["email"]
        response = self.client.post(REGISTER_URL, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_invalid_email_format_returns_400(self):
        response = self.client.post(
            REGISTER_URL,
            {**VALID_REGISTER_PAYLOAD, "email": "not-an-email"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_mismatched_passwords_returns_error(self):
        response = self.client.post(
            REGISTER_URL,
            {**VALID_REGISTER_PAYLOAD, "confirm_password": "DifferentPass789!"},
            format="json",
        )
        self.assertIn(response.status_code, [400, 422])

    def test_duplicate_email_returns_409(self):
        make_user(email="jane@example.com")
        response = self.client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 409)

    def test_registration_disabled_returns_403(self):
        from apps.configurations.models import Configuration

        Configuration.objects.filter(config_code="ALLOW_REGISTRATION").update(
            value="false"
        )
        response = self.client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 403)

    def test_empty_payload_returns_400(self):
        response = self.client.post(REGISTER_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_error_response_success_flag_is_false(self):
        response = self.client.post(REGISTER_URL, {}, format="json")
        self.assertFalse(response.data["success"])


# ---------------------------------------------------------------------------
# POST /api/v1/auth/forgot-password/ — SSO user cannot reset password
# ---------------------------------------------------------------------------


class ForgotPasswordSSOUserAPITest(TestCase):
    def setUp(self):
        from django.contrib.contenttypes.models import ContentType

        from apps.oauth.models import OAuth
        from apps.users.models import UserProfile

        self.client = APIClient()
        self.user = make_user(email="sso@example.com")

        provider = OAuth.objects.create(
            name="SSO API Provider",
            client_id="cid",
            client_secret="csecret",
            auth_endpoint="https://idp.example.com/auth",
            token_endpoint="https://idp.example.com/token",
            userinfo_endpoint="https://idp.example.com/userinfo",
            scope="openid email",
        )
        ct = ContentType.objects.get_for_model(provider)
        UserProfile.objects.create(
            user=self.user,
            sso_provider_content_type=ct,
            sso_provider_object_id=provider.pk,
            sso_uid="sso-uid-api",
        )

    def test_sso_user_password_reset_request_returns_422(self):
        response = self.client.post(
            FP_REQUEST_URL, {"email": "sso@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, 422)

    def test_sso_user_password_reset_response_success_is_false(self):
        response = self.client.post(
            FP_REQUEST_URL, {"email": "sso@example.com"}, format="json"
        )
        self.assertFalse(response.data["success"])


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register/ — non-classic auth mode blocks registration
# ---------------------------------------------------------------------------


class RegisterNonClassicAuthModeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_registration_blocked_when_auth_mode_is_saml(self):
        from apps.configurations.models import Configuration

        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")
        response = self.client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 403)

    def test_registration_blocked_when_auth_mode_is_oauth(self):
        from apps.configurations.models import Configuration

        Configuration.objects.filter(config_code="AUTH_MODE").update(value="oauth")
        response = self.client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 403)

    def test_registration_blocked_response_success_is_false(self):
        from apps.configurations.models import Configuration

        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")
        response = self.client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD, format="json")
        self.assertFalse(response.data["success"])


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me/ — unauthenticated
# ---------------------------------------------------------------------------


class MeGetUnauthenticatedTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_returns_401(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me/ — authenticated
# ---------------------------------------------------------------------------


class MeGetAuthenticatedTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(
            email="me@example.com",
            first_name="Ada",
            last_name="Lovelace",
        )
        token = UserTokenService(user=self.user, request=None).create_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_returns_200(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_success_is_true(self):
        response = self.client.get(ME_URL)
        self.assertTrue(response.data["success"])

    def test_response_contains_first_name(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.data["data"]["first_name"], "Ada")

    def test_response_contains_last_name(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.data["data"]["last_name"], "Lovelace")

    def test_response_contains_email(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.data["data"]["email"], "me@example.com")

    def test_response_contains_theme(self):
        response = self.client.get(ME_URL)
        self.assertIn("theme", response.data["data"])

    def test_default_theme_is_light(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.data["data"]["theme"], "light")

    def test_returns_profile_theme_when_profile_exists(self):
        make_profile(user=self.user, theme="dark")
        response = self.client.get(ME_URL)
        self.assertEqual(response.data["data"]["theme"], "dark")


# PATCH /api/v1/users/me/ tests are in apps/users/tests/integration/test_api.py
