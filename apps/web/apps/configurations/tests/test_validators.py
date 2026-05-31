from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.configurations.validators import CONFIG_CODE_VALIDATOR


class ConfigCodeValidatorTest(SimpleTestCase):
    def test_accepts_single_uppercase_letter(self):
        CONFIG_CODE_VALIDATOR("A")

    def test_accepts_uppercase_word(self):
        CONFIG_CODE_VALIDATOR("APPNAME")

    def test_accepts_uppercase_with_underscores(self):
        CONFIG_CODE_VALIDATOR("APP_NAME")

    def test_accepts_uppercase_with_trailing_digits(self):
        CONFIG_CODE_VALIDATOR("APP1")

    def test_accepts_complex_code(self):
        CONFIG_CODE_VALIDATOR("SETUP_COMPLETE_V2")

    def test_rejects_all_lowercase(self):
        with self.assertRaises(ValidationError):
            CONFIG_CODE_VALIDATOR("app_name")

    def test_rejects_mixed_case(self):
        with self.assertRaises(ValidationError):
            CONFIG_CODE_VALIDATOR("AppName")

    def test_rejects_leading_digit(self):
        with self.assertRaises(ValidationError):
            CONFIG_CODE_VALIDATOR("1APP")

    def test_rejects_hyphen(self):
        with self.assertRaises(ValidationError):
            CONFIG_CODE_VALIDATOR("APP-NAME")

    def test_rejects_space(self):
        with self.assertRaises(ValidationError):
            CONFIG_CODE_VALIDATOR("APP NAME")

    def test_rejects_empty_string(self):
        with self.assertRaises(ValidationError):
            CONFIG_CODE_VALIDATOR("")

    def test_error_code_is_invalid_config_code(self):
        try:
            CONFIG_CODE_VALIDATOR("invalid_code")
        except ValidationError as exc:
            self.assertEqual(exc.code, "invalid_config_code")
        else:
            self.fail("Expected ValidationError was not raised")
