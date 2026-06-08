from unittest.mock import patch

from django.test import TestCase

from apps.configurations.models import Configuration
from apps.configurations.services import (
    AdminConfigurationService,
    ConfigurationService,
)
from apps.core.exceptions import NotFoundException
from apps.users.models import User


class SetConfigCreationTest(TestCase):
    def test_creates_configuration_in_db(self):
        svc = AdminConfigurationService()
        svc.set_config(config_code="APP_NAME", value="TestApp")
        self.assertTrue(Configuration.objects.filter(config_code="APP_NAME").exists())

    def test_returns_configuration_instance(self):
        svc = AdminConfigurationService()
        result = svc.set_config(config_code="APP_NAME", value="TestApp")
        self.assertIsInstance(result, Configuration)

    def test_stores_provided_value(self):
        svc = AdminConfigurationService()
        obj = svc.set_config(config_code="APP_NAME", value="CustomName")
        obj.refresh_from_db()
        self.assertEqual(obj.value, "CustomName")

    def test_sets_label_from_defaults(self):
        svc = AdminConfigurationService()
        obj = svc.set_config(config_code="APP_NAME", value="X")
        self.assertEqual(obj.label, "Application Name")

    def test_sets_module_from_defaults(self):
        svc = AdminConfigurationService()
        obj = svc.set_config(config_code="SETUP_COMPLETE", value="true")
        self.assertEqual(obj.module, "setup")

    def test_raises_not_found_for_unknown_config_code(self):
        svc = AdminConfigurationService()
        with self.assertRaises(NotFoundException):
            svc.set_config(config_code="NONEXISTENT_CODE", value="x")

    def test_does_not_set_created_by_when_no_user(self):
        svc = AdminConfigurationService()
        obj = svc.set_config(config_code="APP_NAME", value="X")
        obj.refresh_from_db()
        self.assertIsNone(obj.created_by)

    def test_sets_created_by_when_user_provided(self):
        # Delete the seeded record so set_config performs
        # a true creation (created=True).
        Configuration.objects.filter(config_code="APP_NAME").delete()
        user = User.objects.create_user(
            username="admin@example.com", email="admin@example.com", password="pass"
        )
        svc = AdminConfigurationService(user=user)
        obj = svc.set_config(config_code="APP_NAME", value="X")
        obj.refresh_from_db()
        self.assertEqual(obj.created_by, user)


class SetConfigUpdateTest(TestCase):
    def test_updates_existing_configuration_value(self):
        svc = AdminConfigurationService()
        svc.set_config(config_code="APP_NAME", value="First")
        svc.set_config(config_code="APP_NAME", value="Second")
        self.assertEqual(
            Configuration.objects.filter(config_code="APP_NAME").count(), 1
        )
        obj = Configuration.objects.get(config_code="APP_NAME")
        self.assertEqual(obj.value, "Second")

    def test_sets_updated_by_when_user_provided(self):
        user = User.objects.create_user(
            username="editor@example.com", email="editor@example.com", password="pass"
        )
        AdminConfigurationService().set_config(config_code="APP_NAME", value="First")
        obj = AdminConfigurationService(user=user).set_config(
            config_code="APP_NAME", value="Updated"
        )
        obj.refresh_from_db()
        self.assertEqual(obj.updated_by, user)


class SetConfigSecretTest(TestCase):
    @patch("apps.configurations.services.encrypt_value", return_value="enc:cipher")
    @patch("apps.configurations.services.Infra.get_secrets_prefix", return_value="")
    def test_encrypts_non_empty_secret_value(self, _prefix, _enc):
        svc = AdminConfigurationService()
        obj = svc.set_config(config_code="EMAIL_SMTP_PASSWORD", value="mysecret")
        obj.refresh_from_db()
        self.assertEqual(obj.value, "enc:cipher")

    @patch("apps.configurations.services.encrypt_value")
    def test_skips_encryption_for_empty_secret_value(self, mock_enc):
        svc = AdminConfigurationService()
        obj = svc.set_config(config_code="EMAIL_SMTP_PASSWORD", value="")
        mock_enc.assert_not_called()
        obj.refresh_from_db()
        self.assertEqual(obj.value, "")

    @patch("apps.configurations.services.encrypt_value")
    def test_skips_encryption_for_non_secret_config(self, mock_enc):
        AdminConfigurationService().set_config(config_code="APP_NAME", value="plain")
        mock_enc.assert_not_called()

    @patch("apps.configurations.services.encrypt_value", return_value="enc:cipher")
    @patch(
        "apps.configurations.services.Infra.get_secrets_prefix", return_value="myapp"
    )
    def test_builds_secret_name_from_prefix_and_config_code(self, _prefix, mock_enc):
        AdminConfigurationService().set_config(
            config_code="EMAIL_SMTP_PASSWORD", value="secret"
        )
        mock_enc.assert_called_once_with("secret", "myapp/EMAIL_SMTP_PASSWORD")


class ConfigurationServiceNotImplementedTest(TestCase):
    def test_create_raises_not_implemented(self):
        svc = ConfigurationService()
        with self.assertRaises(NotImplementedError):
            svc.create()

    def test_update_raises_not_implemented(self):
        svc = ConfigurationService()
        with self.assertRaises(NotImplementedError):
            svc.update(pk=1)

    def test_delete_raises_not_implemented(self):
        svc = ConfigurationService()
        with self.assertRaises(NotImplementedError):
            svc.delete(pk=1)
