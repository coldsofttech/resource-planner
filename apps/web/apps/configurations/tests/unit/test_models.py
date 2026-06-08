from django.test import SimpleTestCase

from apps.configurations.constants import DataType, Module
from apps.configurations.models import Configuration


def _make_unsaved(**kwargs) -> Configuration:
    defaults: dict = {"config_code": "TEST_UNIT", "label": "Unit Test Config"}
    defaults.update(kwargs)
    return Configuration(**defaults)


# ── Configuration.__str__ ──────────────────────────────────────────────────────


class ConfigurationStrUnitTest(SimpleTestCase):
    def test_str_for_non_secret_shows_value(self):
        config = _make_unsaved(value="MyApp", is_secret=False)
        self.assertIn("MyApp", str(config))
        self.assertNotIn("••••••••", str(config))

    def test_str_for_non_secret_with_empty_value_does_not_mask(self):
        config = _make_unsaved(value="", is_secret=False)
        self.assertNotIn("••••••••", str(config))

    def test_str_for_secret_with_value_masks_content(self):
        config = _make_unsaved(value="supersecret", is_secret=True)
        self.assertIn("••••••••", str(config))
        self.assertNotIn("supersecret", str(config))

    def test_str_for_secret_with_empty_value_does_not_mask(self):
        config = _make_unsaved(value="", is_secret=True)
        self.assertNotIn("••••••••", str(config))


# ── Configuration field defaults ───────────────────────────────────────────────


class ConfigurationFieldDefaultsUnitTest(SimpleTestCase):
    def test_data_type_defaults_to_string(self):
        config = _make_unsaved()
        self.assertEqual(config.data_type, DataType.STRING)

    def test_is_secret_defaults_to_false(self):
        config = _make_unsaved()
        self.assertFalse(config.is_secret)

    def test_is_admin_defaults_to_false(self):
        config = _make_unsaved()
        self.assertFalse(config.is_admin)

    def test_module_defaults_to_general(self):
        config = _make_unsaved()
        self.assertEqual(config.module, Module.GENERAL)

    def test_value_defaults_to_empty_string(self):
        config = _make_unsaved()
        self.assertEqual(config.value, "")
