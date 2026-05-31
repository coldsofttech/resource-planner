import os
from unittest.mock import patch

from django.test import TestCase

from apps.auth.constants import AuthMode
from apps.configurations.models import Configuration
from apps.configurations.selectors import (
    Auth,
    Email,
    General,
    Infra,
    Setup,
    get_config_id,
    get_config_value,
)
from apps.setup.constants import DeploymentType, EmailType


def set_config(config_code, value="", **overrides):
    """Update the already-seeded configuration record (or create if absent)."""
    obj, _ = Configuration.objects.update_or_create(
        config_code=config_code,
        defaults={"value": value, **overrides},
    )
    return obj


class GetConfigIdTest(TestCase):
    def test_returns_code_for_existing_config(self):
        # APP_NAME is seeded on every test run — use it directly.
        config = Configuration.objects.get(config_code="APP_NAME")
        result = get_config_id("APP_NAME")
        self.assertEqual(result, config.code)

    def test_raises_does_not_exist_for_unknown_code(self):
        with self.assertRaises(Configuration.DoesNotExist):
            get_config_id("NONEXISTENT_CODE")


class GetConfigValueTest(TestCase):
    def test_returns_value_from_db(self):
        Configuration.objects.filter(config_code="APP_NAME").update(value="MyApp")
        self.assertEqual(get_config_value("APP_NAME"), "MyApp")

    def test_falls_back_to_default_when_not_in_db(self):
        Configuration.objects.filter(config_code="APP_NAME").delete()
        result = get_config_value("APP_NAME")
        self.assertEqual(result, "Resource<b>Planner</b>")

    def test_raises_when_fallback_disabled_and_not_in_db(self):
        Configuration.objects.filter(config_code="APP_NAME").delete()
        with self.assertRaises(Configuration.DoesNotExist):
            get_config_value("APP_NAME", fallback_default=False)

    def test_raises_when_config_code_not_in_db_or_defaults(self):
        with self.assertRaises(Configuration.DoesNotExist):
            get_config_value("NONEXISTENT_CODE")

    def test_returns_plain_secret_without_prefix_unchanged(self):
        Configuration.objects.filter(config_code="EMAIL_SMTP_PASSWORD").update(
            value="plaintext", is_secret=True
        )
        self.assertEqual(get_config_value("EMAIL_SMTP_PASSWORD"), "plaintext")

    @patch("apps.configurations.selectors.fernet_decrypt", return_value="decrypted")
    def test_decrypts_enc_prefixed_secret_when_fernet_key_set(self, mock_decrypt):
        Configuration.objects.filter(config_code="EMAIL_SMTP_PASSWORD").update(
            value="enc:ciphertext", is_secret=True
        )
        with patch.dict(os.environ, {"FERNET_KEY": "fake-fernet-key"}):
            result = get_config_value("EMAIL_SMTP_PASSWORD")
        mock_decrypt.assert_called_once_with("enc:ciphertext", "fake-fernet-key")
        self.assertEqual(result, "decrypted")

    @patch("apps.configurations.selectors.fernet_decrypt")
    def test_skips_decryption_when_fernet_key_not_set(self, mock_decrypt):
        Configuration.objects.filter(config_code="EMAIL_SMTP_PASSWORD").update(
            value="enc:ciphertext", is_secret=True
        )
        env_without_key = {k: v for k, v in os.environ.items() if k != "FERNET_KEY"}
        with patch.dict(os.environ, env_without_key, clear=True):
            result = get_config_value("EMAIL_SMTP_PASSWORD")
        mock_decrypt.assert_not_called()
        self.assertEqual(result, "enc:ciphertext")


class GeneralSelectorTest(TestCase):
    def test_get_app_name_returns_value_from_db(self):
        Configuration.objects.filter(config_code="APP_NAME").update(value="TestApp")
        self.assertEqual(General.get_app_name(), "TestApp")

    def test_get_app_name_falls_back_to_default(self):
        Configuration.objects.filter(config_code="APP_NAME").delete()
        self.assertEqual(General.get_app_name(), "Resource<b>Planner</b>")

    def test_get_app_url_returns_value_from_db(self):
        Configuration.objects.filter(config_code="APP_URL").update(
            value="https://example.com"
        )
        self.assertEqual(General.get_app_url(), "https://example.com")


class SetupSelectorTest(TestCase):
    def test_get_setup_complete_returns_false_by_default(self):
        # Seeded default value is "false".
        self.assertFalse(Setup.get_setup_complete())

    def test_get_setup_complete_returns_true_when_set(self):
        Configuration.objects.filter(config_code="SETUP_COMPLETE").update(value="true")
        self.assertTrue(Setup.get_setup_complete())

    def test_get_setup_complete_returns_false_for_false_value(self):
        Configuration.objects.filter(config_code="SETUP_COMPLETE").update(value="false")
        self.assertFalse(Setup.get_setup_complete())

    def test_is_setup_complete_mirrors_get_setup_complete(self):
        Configuration.objects.filter(config_code="SETUP_COMPLETE").update(value="true")
        self.assertEqual(Setup.is_setup_complete(), Setup.get_setup_complete())


class AuthSelectorTest(TestCase):
    def test_get_auth_mode_falls_back_to_classic(self):
        # Seeded default value is "classic".
        self.assertEqual(Auth.get_auth_mode(), AuthMode.CLASSIC)

    def test_get_auth_mode_returns_mode_from_db(self):
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="classic")
        self.assertEqual(Auth.get_auth_mode(), AuthMode.CLASSIC)

    def test_get_allow_registration_returns_true(self):
        # Seeded default value is "true".
        self.assertTrue(Auth.get_allow_registration())

    def test_get_allow_registration_returns_false(self):
        Configuration.objects.filter(config_code="ALLOW_REGISTRATION").update(
            value="false"
        )
        self.assertFalse(Auth.get_allow_registration())

    def test_is_self_registration_allowed_true_for_classic_with_registration(self):
        # Both seeded defaults already satisfy this condition.
        self.assertTrue(Auth.is_self_registration_allowed())

    def test_is_self_registration_allowed_false_for_classic_without_registration(self):
        Configuration.objects.filter(config_code="ALLOW_REGISTRATION").update(
            value="false"
        )
        self.assertFalse(Auth.is_self_registration_allowed())


class AuthSelectorSAMLOAuthTest(TestCase):
    def test_get_auth_mode_returns_saml(self):
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")
        self.assertEqual(Auth.get_auth_mode(), AuthMode.SAML)

    def test_get_auth_mode_returns_oauth(self):
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="oauth")
        self.assertEqual(Auth.get_auth_mode(), AuthMode.OAUTH)

    def test_is_self_registration_not_allowed_for_saml_mode(self):
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="saml")
        self.assertFalse(Auth.is_self_registration_allowed())

    def test_is_self_registration_not_allowed_for_oauth_mode(self):
        Configuration.objects.filter(config_code="AUTH_MODE").update(value="oauth")
        self.assertFalse(Auth.is_self_registration_allowed())


class InfraSelectorTest(TestCase):
    def test_get_deployment_type_falls_back_to_local(self):
        # Seeded default value is "local".
        self.assertEqual(Infra.get_deployment_type(), DeploymentType.LOCAL)

    def test_get_deployment_type_returns_value_from_db(self):
        Configuration.objects.filter(config_code="DEPLOYMENT_TYPE").update(
            value="local"
        )
        self.assertEqual(Infra.get_deployment_type(), DeploymentType.LOCAL)

    def test_get_secrets_prefix_strips_trailing_slash(self):
        Configuration.objects.filter(config_code="SECRETS_PREFIX").update(
            value="myapp/"
        )
        self.assertEqual(Infra.get_secrets_prefix(), "myapp")

    def test_get_secrets_prefix_returns_empty_by_default(self):
        # Seeded default value is "".
        self.assertEqual(Infra.get_secrets_prefix(), "")

    def test_get_storage_type_returns_database_by_default(self):
        from apps.setup.constants import StorageType

        self.assertEqual(Infra.get_storage_type(), StorageType.DATABASE)

    def test_get_storage_type_returns_filesystem_when_set(self):
        from apps.setup.constants import StorageType

        Configuration.objects.filter(config_code="STORAGE_TYPE").update(
            value="filesystem"
        )
        self.assertEqual(Infra.get_storage_type(), StorageType.FILE_SYSTEM)

    def test_get_storage_path_returns_empty_by_default(self):
        self.assertEqual(Infra.get_storage_path(), "")

    def test_get_storage_path_returns_configured_value(self):
        Configuration.objects.filter(config_code="STORAGE_PATH").update(
            value="/var/data/uploads"
        )
        self.assertEqual(Infra.get_storage_path(), "/var/data/uploads")


class EmailSelectorTest(TestCase):
    def test_get_email_type_returns_value_from_db(self):
        # Seeded default value is "console".
        self.assertEqual(Email.get_email_type(), EmailType.CONSOLE)

    def test_get_smtp_port_returns_int(self):
        # Seeded default value is "587".
        self.assertEqual(Email.get_smtp_port(), 587)

    def test_get_email_from_address_returns_configured_value(self):
        Configuration.objects.filter(config_code="EMAIL_FROM_ADDRESS").update(
            value="noreply@example.com"
        )
        self.assertEqual(Email.get_email_from_address(), "noreply@example.com")

    def test_get_email_from_name_returns_configured_value(self):
        Configuration.objects.filter(config_code="EMAIL_FROM_NAME").update(
            value="My App"
        )
        self.assertEqual(Email.get_email_from_name(), "My App")

    def test_is_smtp_auth_enabled_returns_false(self):
        # Seeded default value is "false".
        self.assertFalse(Email.is_smtp_auth_enabled())

    def test_is_smtp_auth_enabled_returns_true(self):
        Configuration.objects.filter(config_code="EMAIL_SMTP_AUTH_ENABLED").update(
            value="true"
        )
        self.assertTrue(Email.is_smtp_auth_enabled())

    def test_get_smtp_host_returns_empty_by_default(self):
        self.assertEqual(Email.get_smtp_host(), "")

    def test_get_smtp_host_returns_configured_value(self):
        Configuration.objects.filter(config_code="EMAIL_SMTP_HOST").update(
            value="smtp.example.com"
        )
        self.assertEqual(Email.get_smtp_host(), "smtp.example.com")

    def test_get_smtp_enc_type_returns_none_by_default(self):
        self.assertEqual(Email.get_smtp_enc_type(), "none")

    def test_get_smtp_enc_type_returns_configured_value(self):
        Configuration.objects.filter(config_code="EMAIL_SMTP_ENC_TYPE").update(
            value="starttls"
        )
        self.assertEqual(Email.get_smtp_enc_type(), "starttls")

    def test_get_smtp_username_returns_empty_by_default(self):
        self.assertEqual(Email.get_smtp_username(), "")

    def test_get_smtp_username_returns_configured_value(self):
        Configuration.objects.filter(config_code="EMAIL_SMTP_USERNAME").update(
            value="smtpuser"
        )
        self.assertEqual(Email.get_smtp_username(), "smtpuser")
