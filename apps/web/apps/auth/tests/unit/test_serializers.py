from django.test import SimpleTestCase

from apps.auth.serializers import (
    ForgotPasswordRequestSerializer,
    ForgotPasswordResetSerializer,
    ForgotPasswordVerifySerializer,
    LoginSerializer,
    RegisterSerializer,
)

# ---------------------------------------------------------------------------
# LoginSerializer
# ---------------------------------------------------------------------------

VALID_LOGIN = {
    "email": "user@example.com",
    "password": "securepassword",
}


class LoginSerializerValidationTest(SimpleTestCase):
    def test_valid_data_passes(self):
        s = LoginSerializer(data=VALID_LOGIN)
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_email_fails(self):
        data = {**VALID_LOGIN}
        del data["email"]
        s = LoginSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_missing_password_fails(self):
        data = {**VALID_LOGIN}
        del data["password"]
        s = LoginSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("password", s.errors)

    def test_invalid_email_format_fails(self):
        s = LoginSerializer(data={**VALID_LOGIN, "email": "not-an-email"})
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_empty_string_email_fails(self):
        s = LoginSerializer(data={**VALID_LOGIN, "email": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_empty_string_password_fails(self):
        s = LoginSerializer(data={**VALID_LOGIN, "password": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("password", s.errors)

    def test_empty_payload_fails(self):
        s = LoginSerializer(data={})
        self.assertFalse(s.is_valid())

    def test_valid_data_exposes_email(self):
        s = LoginSerializer(data=VALID_LOGIN)
        s.is_valid()
        self.assertEqual(s.validated_data["email"], "user@example.com")

    def test_valid_data_exposes_password(self):
        s = LoginSerializer(data=VALID_LOGIN)
        s.is_valid()
        self.assertEqual(s.validated_data["password"], "securepassword")


# ---------------------------------------------------------------------------
# ForgotPasswordRequestSerializer
# ---------------------------------------------------------------------------


class ForgotPasswordRequestSerializerTest(SimpleTestCase):
    def test_valid_email_passes(self):
        s = ForgotPasswordRequestSerializer(data={"email": "user@example.com"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_email_fails(self):
        s = ForgotPasswordRequestSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_invalid_email_format_fails(self):
        s = ForgotPasswordRequestSerializer(data={"email": "not-an-email"})
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_empty_string_email_fails(self):
        s = ForgotPasswordRequestSerializer(data={"email": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_validated_data_contains_email(self):
        s = ForgotPasswordRequestSerializer(data={"email": "user@example.com"})
        s.is_valid()
        self.assertEqual(s.validated_data["email"], "user@example.com")


# ---------------------------------------------------------------------------
# ForgotPasswordVerifySerializer
# ---------------------------------------------------------------------------

VALID_VERIFY = {
    "email": "user@example.com",
    "code": "123456",
}


class ForgotPasswordVerifySerializerTest(SimpleTestCase):
    def test_valid_data_passes(self):
        s = ForgotPasswordVerifySerializer(data=VALID_VERIFY)
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_email_fails(self):
        s = ForgotPasswordVerifySerializer(data={"code": "123456"})
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_missing_code_fails(self):
        s = ForgotPasswordVerifySerializer(data={"email": "user@example.com"})
        self.assertFalse(s.is_valid())
        self.assertIn("code", s.errors)

    def test_code_shorter_than_6_fails(self):
        s = ForgotPasswordVerifySerializer(data={**VALID_VERIFY, "code": "12345"})
        self.assertFalse(s.is_valid())
        self.assertIn("code", s.errors)

    def test_code_longer_than_6_fails(self):
        s = ForgotPasswordVerifySerializer(data={**VALID_VERIFY, "code": "1234567"})
        self.assertFalse(s.is_valid())
        self.assertIn("code", s.errors)

    def test_empty_payload_fails(self):
        s = ForgotPasswordVerifySerializer(data={})
        self.assertFalse(s.is_valid())

    def test_all_zeros_code_passes(self):
        s = ForgotPasswordVerifySerializer(data={**VALID_VERIFY, "code": "000000"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_alphanumeric_code_passes(self):
        s = ForgotPasswordVerifySerializer(data={**VALID_VERIFY, "code": "abc123"})
        self.assertTrue(s.is_valid(), s.errors)


# ---------------------------------------------------------------------------
# ForgotPasswordResetSerializer
# ---------------------------------------------------------------------------

VALID_RESET = {
    "email": "user@example.com",
    "code": "123456",
    "new_password": "NewSecurePass456!",
    "confirm_password": "NewSecurePass456!",
}


class ForgotPasswordResetSerializerTest(SimpleTestCase):
    def test_valid_data_passes(self):
        s = ForgotPasswordResetSerializer(data=VALID_RESET)
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_email_fails(self):
        data = {**VALID_RESET}
        del data["email"]
        s = ForgotPasswordResetSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_missing_code_fails(self):
        data = {**VALID_RESET}
        del data["code"]
        s = ForgotPasswordResetSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("code", s.errors)

    def test_missing_new_password_fails(self):
        data = {**VALID_RESET}
        del data["new_password"]
        s = ForgotPasswordResetSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("new_password", s.errors)

    def test_missing_confirm_password_fails(self):
        data = {**VALID_RESET}
        del data["confirm_password"]
        s = ForgotPasswordResetSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("confirm_password", s.errors)

    def test_new_password_shorter_than_12_fails(self):
        s = ForgotPasswordResetSerializer(
            data={
                **VALID_RESET,
                "new_password": "Short1!",
                "confirm_password": "Short1!",
            }
        )
        self.assertFalse(s.is_valid())

    def test_numeric_only_password_fails_django_validator(self):
        s = ForgotPasswordResetSerializer(
            data={
                **VALID_RESET,
                "new_password": "123456789012",
                "confirm_password": "123456789012",
            }
        )
        self.assertFalse(s.is_valid())

    def test_mismatched_passwords_fails(self):
        s = ForgotPasswordResetSerializer(
            data={**VALID_RESET, "confirm_password": "DifferentPass789!"}
        )
        self.assertFalse(s.is_valid())

    def test_mismatched_passwords_error_is_on_confirm_password_or_non_field(self):
        s = ForgotPasswordResetSerializer(
            data={**VALID_RESET, "confirm_password": "DifferentPass789!"}
        )
        s.is_valid()
        self.assertTrue(
            "confirm_password" in s.errors or "non_field_errors" in s.errors
        )

    def test_empty_payload_fails(self):
        s = ForgotPasswordResetSerializer(data={})
        self.assertFalse(s.is_valid())


# ---------------------------------------------------------------------------
# RegisterSerializer
# ---------------------------------------------------------------------------

VALID_REGISTER = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "password": "SecureRegPass123!",
    "confirm_password": "SecureRegPass123!",
}


class RegisterSerializerValidationTest(SimpleTestCase):
    def test_valid_data_passes(self):
        s = RegisterSerializer(data=VALID_REGISTER)
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_first_name_fails(self):
        data = {**VALID_REGISTER}
        del data["first_name"]
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("first_name", s.errors)

    def test_missing_last_name_fails(self):
        data = {**VALID_REGISTER}
        del data["last_name"]
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("last_name", s.errors)

    def test_missing_email_fails(self):
        data = {**VALID_REGISTER}
        del data["email"]
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_invalid_email_format_fails(self):
        s = RegisterSerializer(data={**VALID_REGISTER, "email": "not-an-email"})
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_missing_password_fails(self):
        data = {**VALID_REGISTER}
        del data["password"]
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("password", s.errors)

    def test_password_shorter_than_12_fails(self):
        s = RegisterSerializer(
            data={
                **VALID_REGISTER,
                "password": "Short1!",
                "confirm_password": "Short1!",
            }
        )
        self.assertFalse(s.is_valid())

    def test_numeric_only_password_fails_django_validator(self):
        s = RegisterSerializer(
            data={
                **VALID_REGISTER,
                "password": "123456789012",
                "confirm_password": "123456789012",
            }
        )
        self.assertFalse(s.is_valid())

    def test_missing_confirm_password_fails(self):
        data = {**VALID_REGISTER}
        del data["confirm_password"]
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("confirm_password", s.errors)

    def test_mismatched_passwords_fails(self):
        s = RegisterSerializer(
            data={**VALID_REGISTER, "confirm_password": "DifferentPass789!"}
        )
        self.assertFalse(s.is_valid())

    def test_empty_payload_fails(self):
        s = RegisterSerializer(data={})
        self.assertFalse(s.is_valid())

    def test_empty_first_name_fails(self):
        s = RegisterSerializer(data={**VALID_REGISTER, "first_name": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("first_name", s.errors)

    def test_whitespace_only_first_name_fails(self):
        s = RegisterSerializer(data={**VALID_REGISTER, "first_name": "   "})
        self.assertFalse(s.is_valid())
        self.assertIn("first_name", s.errors)

    def test_whitespace_only_last_name_fails(self):
        s = RegisterSerializer(data={**VALID_REGISTER, "last_name": "   "})
        self.assertFalse(s.is_valid())
        self.assertIn("last_name", s.errors)

    def test_validated_data_contains_all_fields(self):
        s = RegisterSerializer(data=VALID_REGISTER)
        s.is_valid()
        for field in ["first_name", "last_name", "email", "password"]:
            self.assertIn(field, s.validated_data)
