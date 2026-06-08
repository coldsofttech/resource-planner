from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.configurations.constants import DataType, Module
from apps.configurations.models import Configuration
from apps.users.models import User

# Use codes NOT in CONFIGURATION_DEFAULTS so they don't conflict with seeded records.
_CODE_A = "TEST_CONF_A"
_CODE_B = "TEST_CONF_B"
_CODE_C = "TEST_CONF_C"
_CODE_SEC = "TEST_CONF_SEC"


def make_config(config_code=_CODE_A, label="Test Config", **overrides):
    return Configuration.objects.create(
        config_code=config_code, label=label, **overrides
    )


class ConfigurationCodeTest(TestCase):
    def test_code_auto_generated_with_config_prefix(self):
        config = make_config()
        self.assertTrue(config.code.startswith("CONFIG-"))

    def test_code_contains_primary_key(self):
        config = make_config()
        self.assertEqual(config.code, f"CONFIG-{config.pk}")

    def test_each_configuration_gets_unique_code(self):
        c1 = make_config(config_code=_CODE_A)
        c2 = make_config(config_code=_CODE_B)
        self.assertNotEqual(c1.code, c2.code)


class ConfigurationStrTest(TestCase):
    def test_str_for_non_secret_shows_value(self):
        config = make_config(config_code=_CODE_A, value="MyApp")
        self.assertIn("MyApp", str(config))
        self.assertNotIn("••••••••", str(config))

    def test_str_for_non_secret_with_empty_value(self):
        config = make_config(config_code=_CODE_A, value="")
        self.assertIn("CONFIG-", str(config))
        self.assertNotIn("••••••••", str(config))

    def test_str_for_secret_with_value_masks_content(self):
        config = make_config(
            config_code=_CODE_SEC,
            value="supersecret",
            is_secret=True,
        )
        self.assertIn("••••••••", str(config))
        self.assertNotIn("supersecret", str(config))

    def test_str_for_secret_with_empty_value_does_not_mask(self):
        config = make_config(
            config_code=_CODE_SEC,
            value="",
            is_secret=True,
        )
        self.assertNotIn("••••••••", str(config))


class ConfigurationFieldDefaultsTest(TestCase):
    def test_data_type_defaults_to_string(self):
        config = make_config()
        self.assertEqual(config.data_type, DataType.STRING)

    def test_is_secret_defaults_to_false(self):
        config = make_config()
        self.assertFalse(config.is_secret)

    def test_is_admin_defaults_to_false(self):
        config = make_config()
        self.assertFalse(config.is_admin)

    def test_module_defaults_to_general(self):
        config = make_config()
        self.assertEqual(config.module, Module.GENERAL)

    def test_value_defaults_to_empty_string(self):
        config = make_config()
        self.assertEqual(config.value, "")

    def test_created_at_is_set_on_creation(self):
        config = make_config()
        self.assertIsNotNone(config.created_at)

    def test_updated_at_is_set_on_creation(self):
        config = make_config()
        self.assertIsNotNone(config.updated_at)


class ConfigurationConstraintsTest(TestCase):
    def test_duplicate_config_code_raises_integrity_error(self):
        make_config(config_code=_CODE_A)
        with self.assertRaises(IntegrityError):
            make_config(config_code=_CODE_A)

    def test_config_code_validator_rejects_lowercase(self):
        config = Configuration(config_code="app_name", label="Test")
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_config_code_validator_rejects_leading_digit(self):
        config = Configuration(config_code="1APP", label="Test")
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_config_code_validator_rejects_hyphen(self):
        config = Configuration(config_code="APP-NAME", label="Test")
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_config_code_validator_rejects_mixed_case(self):
        config = Configuration(config_code="AppName", label="Test")
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_config_code_validator_accepts_valid_uppercase(self):
        config = Configuration(config_code="VALID_CODE", label="Test", value="")
        config.full_clean()


class ConfigurationOrderingTest(TestCase):
    _CODES = ["TEST_ZZZ", "TEST_AAA", "TEST_MMM"]

    def test_default_ordering_by_config_code(self):
        make_config(config_code="TEST_ZZZ", label="Last")
        make_config(config_code="TEST_AAA", label="First")
        make_config(config_code="TEST_MMM", label="Middle")
        codes = list(
            Configuration.objects.filter(config_code__in=self._CODES).values_list(
                "config_code", flat=True
            )
        )
        self.assertEqual(codes, ["TEST_AAA", "TEST_MMM", "TEST_ZZZ"])


class ConfigurationAuditTest(TestCase):
    def test_created_by_defaults_to_none(self):
        config = make_config()
        self.assertIsNone(config.created_by)

    def test_created_by_can_be_set(self):
        user = User.objects.create_user(
            username="admin@example.com", email="admin@example.com", password="pass"
        )
        config = make_config(created_by=user)
        self.assertEqual(config.created_by, user)

    def test_updated_by_defaults_to_none(self):
        config = make_config()
        self.assertIsNone(config.updated_by)

    def test_updated_by_can_be_set(self):
        user = User.objects.create_user(
            username="editor@example.com", email="editor@example.com", password="pass"
        )
        config = make_config()
        config.updated_by = user
        config.save(update_fields=["updated_by"])
        config.refresh_from_db()
        self.assertEqual(config.updated_by, user)
