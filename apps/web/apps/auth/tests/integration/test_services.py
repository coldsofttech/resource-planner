from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.auth.models import PasswordResetToken
from apps.auth.services import (
    AuthService,
    ForgotPasswordService,
    RegisterService,
    UserTokenService,
)
from apps.auth.tests.factories import make_token
from apps.core.exceptions import (
    AlreadyExistsException,
    AuthFailedException,
    PermissionException,
    ValidationException,
)
from apps.users.models import User
from apps.users.tests.factories import make_superuser, make_user

# ---------------------------------------------------------------------------
# AuthService — classic_login
# ---------------------------------------------------------------------------


class AuthServiceClassicLoginTest(TestCase):
    def setUp(self):
        self.user = make_user()

    @patch("apps.auth.services.auth_login")
    def test_returns_user_for_valid_credentials(self, _login):
        svc = AuthService(user=None, request=None)
        result = svc.classic_login(email="user@example.com", password="StrongPass123!")
        self.assertEqual(result.email, "user@example.com")

    @patch("apps.auth.services.auth_login")
    def test_calls_auth_login_on_success(self, mock_login):
        svc = AuthService(user=None, request=None)
        svc.classic_login(email="user@example.com", password="StrongPass123!")
        mock_login.assert_called_once()

    def test_raises_auth_failed_for_wrong_password(self):
        svc = AuthService(user=None, request=None)
        with self.assertRaises(AuthFailedException):
            svc.classic_login(email="user@example.com", password="wrongpassword")

    def test_raises_auth_failed_for_nonexistent_user(self):
        svc = AuthService(user=None, request=None)
        with self.assertRaises(AuthFailedException):
            svc.classic_login(email="nobody@example.com", password="StrongPass123!")

    def test_raises_permission_for_inactive_user(self):
        make_user(email="inactive@example.com", is_active=False)
        svc = AuthService(user=None, request=None)
        with self.assertRaises(PermissionException):
            svc.classic_login(email="inactive@example.com", password="StrongPass123!")

    @patch(
        "apps.configurations.selectors.Auth.get_auth_mode",
        return_value=__import__(
            "apps.auth.constants", fromlist=["AuthMode"]
        ).AuthMode.SAML,
    )
    def test_raises_validation_for_saml_auth_mode_non_superuser(self, _mode):
        svc = AuthService(user=None, request=None)
        with self.assertRaises(ValidationException):
            svc.classic_login(email="user@example.com", password="StrongPass123!")

    @patch(
        "apps.configurations.selectors.Auth.get_auth_mode",
        return_value=__import__(
            "apps.auth.constants", fromlist=["AuthMode"]
        ).AuthMode.OAUTH,
    )
    def test_raises_validation_for_oauth_auth_mode_non_superuser(self, _mode):
        svc = AuthService(user=None, request=None)
        with self.assertRaises(ValidationException):
            svc.classic_login(email="user@example.com", password="StrongPass123!")

    @patch("apps.auth.services.auth_login")
    @patch(
        "apps.configurations.selectors.Auth.get_auth_mode",
        return_value=__import__(
            "apps.auth.constants", fromlist=["AuthMode"]
        ).AuthMode.SAML,
    )
    def test_superuser_can_login_regardless_of_auth_mode(self, _mode, _login):
        superuser = make_superuser("super@example.com")
        svc = AuthService(user=None, request=None)
        result = svc.classic_login(email="super@example.com", password="StrongPass123!")
        self.assertEqual(result.pk, superuser.pk)


# ---------------------------------------------------------------------------
# UserTokenService — create_token / revoke_current_token
# ---------------------------------------------------------------------------


class UserTokenServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_create_token_returns_user_token(self):
        from apps.auth.models import UserToken

        svc = UserTokenService(user=None, request=None)
        token = svc.create_token(self.user)
        self.assertIsInstance(token, UserToken)

    def test_create_token_is_active(self):
        svc = UserTokenService(user=None, request=None)
        token = svc.create_token(self.user)
        self.assertTrue(token.is_active)

    def test_create_token_linked_to_user(self):
        svc = UserTokenService(user=None, request=None)
        token = svc.create_token(self.user)
        self.assertEqual(token.user, self.user)

    def test_create_token_generates_unique_keys(self):
        svc = UserTokenService(user=None, request=None)
        t1 = svc.create_token(self.user)
        t2 = svc.create_token(self.user)
        self.assertNotEqual(t1.key, t2.key)

    def test_create_token_key_is_64_chars(self):
        svc = UserTokenService(user=None, request=None)
        token = svc.create_token(self.user)
        self.assertEqual(len(token.key), 64)


class UserTokenServiceRevokeTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def _make_mock_request(self, key=None, scheme="Bearer"):
        request = MagicMock()
        if key:
            request.META = {"HTTP_AUTHORIZATION": f"{scheme} {key}"}
        else:
            request.META = {}
        return request

    def test_revoke_deactivates_matching_token(self):
        svc_create = UserTokenService(user=None, request=None)
        token = svc_create.create_token(self.user)

        request = self._make_mock_request(key=token.key)
        svc_revoke = UserTokenService(user=None, request=request)
        svc_revoke.revoke_current_token()

        token.refresh_from_db()
        self.assertFalse(token.is_active)

    def test_revoke_no_op_when_no_authorization_header(self):
        svc_create = UserTokenService(user=None, request=None)
        token = svc_create.create_token(self.user)

        request = self._make_mock_request()
        svc_revoke = UserTokenService(user=None, request=request)
        svc_revoke.revoke_current_token()

        token.refresh_from_db()
        self.assertTrue(token.is_active)

    def test_revoke_no_op_for_unknown_key(self):
        from apps.auth.models import UserToken

        request = self._make_mock_request(key="nonexistentkey" * 5)
        svc = UserTokenService(user=None, request=request)
        svc.revoke_current_token()
        self.assertEqual(UserToken.objects.filter(is_active=False).count(), 0)

    def test_revoke_is_case_insensitive_for_bearer_keyword(self):
        svc_create = UserTokenService(user=None, request=None)
        token = svc_create.create_token(self.user)

        request = self._make_mock_request(key=token.key, scheme="BEARER")
        svc_revoke = UserTokenService(user=None, request=request)
        svc_revoke.revoke_current_token()

        token.refresh_from_db()
        self.assertFalse(token.is_active)


# ---------------------------------------------------------------------------
# ForgotPasswordService — request_password_reset
# ---------------------------------------------------------------------------


class ForgotPasswordServiceRequestTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = ForgotPasswordService(user=None, request=None)

    def test_raises_validation_for_nonexistent_email(self):
        with self.assertRaises(ValidationException):
            self.svc.request_password_reset(email="nobody@example.com")

    def test_raises_validation_for_inactive_user(self):
        make_user(email="inactive@example.com", is_active=False)
        with self.assertRaises(ValidationException):
            self.svc.request_password_reset(email="inactive@example.com")

    @patch("apps.auth.services.build_email_sender")
    def test_creates_password_reset_token(self, mock_sender):
        mock_sender.return_value.send.return_value = None
        self.svc.request_password_reset(email=self.user.email)
        self.assertTrue(
            PasswordResetToken.objects.filter(user=self.user, is_used=False).exists()
        )

    @patch("apps.auth.services.build_email_sender")
    def test_invalidates_old_tokens_before_generating_new(self, mock_sender):
        mock_sender.return_value.send.return_value = None
        make_token(self.user, token_hash="old" * 21 + "x")
        self.svc.request_password_reset(email=self.user.email)
        old_tokens = PasswordResetToken.objects.filter(user=self.user, is_used=True)
        self.assertEqual(old_tokens.count(), 1)

    @patch("apps.auth.services.build_email_sender")
    def test_sends_email_to_user(self, mock_sender):
        mock_send = MagicMock()
        mock_sender.return_value.send = mock_send
        self.svc.request_password_reset(email=self.user.email)
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        self.assertEqual(call_kwargs["to"], self.user.email)

    @patch("apps.auth.services.build_email_sender")
    def test_email_send_failure_does_not_raise(self, mock_sender):
        mock_sender.return_value.send.side_effect = Exception("SMTP error")
        try:
            self.svc.request_password_reset(email=self.user.email)
        except Exception:
            self.fail("request_password_reset raised an exception on email failure")


# ---------------------------------------------------------------------------
# ForgotPasswordService — verify_reset_code
# ---------------------------------------------------------------------------


class ForgotPasswordServiceVerifyTest(TestCase):
    def setUp(self):
        from otpcore import hash_otp

        self.user = make_user()
        self.svc = ForgotPasswordService(user=None, request=None)
        self.valid_code = "654321"
        make_token(self.user, token_hash=hash_otp(self.valid_code))

    def test_returns_true_for_valid_code(self):
        result = self.svc.verify_reset_code(email=self.user.email, code=self.valid_code)
        self.assertTrue(result)

    def test_returns_false_for_wrong_code(self):
        result = self.svc.verify_reset_code(email=self.user.email, code="000000")
        self.assertFalse(result)

    def test_returns_false_for_expired_token(self):
        from otpcore import hash_otp

        expired_code = "111111"
        make_token(
            self.user, token_hash=hash_otp(expired_code), minutes_until_expiry=-1
        )
        result = self.svc.verify_reset_code(email=self.user.email, code=expired_code)
        self.assertFalse(result)

    def test_returns_false_for_used_token(self):
        from otpcore import hash_otp

        used_code = "222222"
        make_token(self.user, token_hash=hash_otp(used_code), is_used=True)
        result = self.svc.verify_reset_code(email=self.user.email, code=used_code)
        self.assertFalse(result)

    def test_returns_false_for_nonexistent_email(self):
        result = self.svc.verify_reset_code(
            email="nobody@example.com", code=self.valid_code
        )
        self.assertFalse(result)

    def test_does_not_consume_token_on_verify(self):
        self.svc.verify_reset_code(email=self.user.email, code=self.valid_code)
        still_active = PasswordResetToken.objects.filter(
            user=self.user, is_used=False
        ).exists()
        self.assertTrue(still_active)


# ---------------------------------------------------------------------------
# ForgotPasswordService — reset_password
# ---------------------------------------------------------------------------


class ForgotPasswordServiceResetTest(TestCase):
    def setUp(self):
        from otpcore import hash_otp

        self.user = make_user()
        self.svc = ForgotPasswordService(user=None, request=None)
        self.valid_code = "789012"
        make_token(self.user, token_hash=hash_otp(self.valid_code))

    def test_resets_password_successfully(self):
        self.svc.reset_password(
            email=self.user.email,
            code=self.valid_code,
            new_password="NewSecurePass456!",
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecurePass456!"))

    def test_raises_validation_for_invalid_code(self):
        with self.assertRaises(ValidationException):
            self.svc.reset_password(
                email=self.user.email,
                code="000000",
                new_password="NewSecurePass456!",
            )

    def test_raises_validation_if_same_as_current_password(self):
        with self.assertRaises(ValidationException):
            self.svc.reset_password(
                email=self.user.email,
                code=self.valid_code,
                new_password="StrongPass123!",
            )

    def test_marks_token_as_used_after_reset(self):
        self.svc.reset_password(
            email=self.user.email,
            code=self.valid_code,
            new_password="NewSecurePass456!",
        )
        token = PasswordResetToken.objects.get(user=self.user)
        self.assertTrue(token.is_used)

    def test_used_token_cannot_be_reused(self):
        self.svc.reset_password(
            email=self.user.email,
            code=self.valid_code,
            new_password="NewSecurePass456!",
        )
        with self.assertRaises(ValidationException):
            self.svc.reset_password(
                email=self.user.email,
                code=self.valid_code,
                new_password="AnotherPass789!",
            )


# ---------------------------------------------------------------------------
# RegisterService — register
# ---------------------------------------------------------------------------


class RegisterServiceTest(TestCase):
    def setUp(self):
        self.svc = RegisterService(user=None, request=None)

    def test_creates_user_successfully(self):
        self.svc.register(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password="StrongPass123!",
        )
        self.assertTrue(User.objects.filter(email="jane@example.com").exists())

    def test_returns_user_instance(self):
        result = self.svc.register(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password="StrongPass123!",
        )
        self.assertIsInstance(result, User)

    def test_created_user_has_correct_email(self):
        user = self.svc.register(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password="StrongPass123!",
        )
        self.assertEqual(user.email, "jane@example.com")

    def test_raises_permission_when_registration_disabled(self):
        from apps.configurations.models import Configuration

        Configuration.objects.filter(config_code="ALLOW_REGISTRATION").update(
            value="false"
        )
        with self.assertRaises(PermissionException):
            self.svc.register(
                first_name="Jane",
                last_name="Doe",
                email="blocked@example.com",
                password="StrongPass123!",
            )

    def test_raises_already_exists_for_duplicate_email(self):
        make_user(email="taken@example.com")
        with self.assertRaises(AlreadyExistsException):
            self.svc.register(
                first_name="Jane",
                last_name="Doe",
                email="taken@example.com",
                password="StrongPass123!",
            )

    def test_raises_permission_when_auth_mode_is_not_classic(self):
        from apps.configurations.models import Configuration

        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")
        with self.assertRaises(PermissionException):
            self.svc.register(
                first_name="Jane",
                last_name="Doe",
                email="samluser@example.com",
                password="StrongPass123!",
            )


# ---------------------------------------------------------------------------
# ForgotPasswordService — SSO users cannot request password reset
# ---------------------------------------------------------------------------


class ForgotPasswordServiceSSOUserTest(TestCase):
    def setUp(self):
        from django.contrib.contenttypes.models import ContentType

        from apps.oauth.models import OAuth
        from apps.users.models import UserProfile

        self.svc = ForgotPasswordService(user=None, request=None)
        self.user = make_user(email="sso@example.com")

        provider = OAuth.objects.create(
            name="SSO Test Provider",
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
            sso_uid="sso-uid-123",
        )

    def test_raises_validation_for_sso_user(self):
        with self.assertRaises(ValidationException):
            self.svc.request_password_reset(email="sso@example.com")

    def test_sso_user_no_reset_token_created(self):
        try:
            self.svc.request_password_reset(email="sso@example.com")
        except ValidationException:
            pass
        from apps.auth.models import PasswordResetToken

        self.assertFalse(PasswordResetToken.objects.filter(user=self.user).exists())
