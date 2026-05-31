from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.auth.models import PasswordResetToken
from apps.users.models import User

LOGIN_URL = "/api/v1/auth/login/"
FP_REQUEST_URL = "/api/v1/auth/forgot-password/"
FP_VERIFY_URL = "/api/v1/auth/forgot-password/verify/"
FP_RESET_URL = "/api/v1/auth/forgot-password/reset/"
REGISTER_URL = "/api/v1/auth/register/"

VALID_CREDENTIALS = {
    "email": "user@example.com",
    "password": "SecurePass123!",
}


def make_user(email="user@example.com", password="SecurePass123!", is_active=True):
    return User.objects.create_user(
        username=email, email=email, password=password, is_active=is_active
    )


def make_token(user, code_hash, minutes=10):
    return PasswordResetToken.objects.create(
        user=user,
        email=user.email,
        token_hash=code_hash,
        expires_at=timezone.now() + timedelta(minutes=minutes),
    )


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
# POST /api/v1/auth/forgot-password/ — request reset
# ---------------------------------------------------------------------------


class ForgotPasswordRequestAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def test_known_email_returns_200(self):
        from unittest.mock import patch

        with patch("apps.auth.services.build_email_sender") as mock_sender:
            mock_sender.return_value.send.return_value = None
            response = self.client.post(
                FP_REQUEST_URL, {"email": self.user.email}, format="json"
            )
        self.assertEqual(response.status_code, 200)

    def test_known_email_response_success_is_true(self):
        from unittest.mock import patch

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
        make_token(self.user, code_hash=hash_otp(self.valid_code))

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
        make_token(self.user, code_hash=hash_otp(expired_code), minutes=-1)
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


# ---------------------------------------------------------------------------
# POST /api/v1/auth/forgot-password/reset/ — reset password
# ---------------------------------------------------------------------------


class ForgotPasswordResetAPITest(TestCase):
    def setUp(self):
        from otpcore import hash_otp

        self.client = APIClient()
        self.user = make_user()
        self.valid_code = "789012"
        make_token(self.user, code_hash=hash_otp(self.valid_code))

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
                "new_password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
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
