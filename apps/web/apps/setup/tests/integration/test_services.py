"""Integration tests for apps.setup services — verifies DB writes after create()."""

import os
from unittest.mock import MagicMock, patch

import pytest

from apps.setup.services import SetupService

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service():
    return SetupService(user=None, request=None)


def _sqlite_classic_payload(*, email="alice@example.com"):
    from cryptography.fernet import Fernet

    return {
        "admin": {
            "first_name": "Alice",
            "last_name": "Admin",
            "email": email,
            "password": "SecurePass123!",
        },
        "app": {
            "app_name": "TestPlanner",
            "app_url": "https://planner.example.com",
        },
        "infra": {
            "deployment_type": "local",
            "fernet_key": Fernet.generate_key().decode(),
        },
        "db": {"engine": "sqlite"},
        "auth": {"auth_type": "classic", "self_register": True},
        "storage": {"storage_type": "database"},
        "email": {
            "email_type": "console",
            "from_address": "noreply@example.com",
            "from_name": "Planner",
        },
        "logging": {
            "log_destination": "local",
            "log_name": "application",
            "log_path": "/tmp/logs",  # nosec B108
        },
    }


def _run_create(svc, payload):
    """
    Call create() with all file/env write methods mocked so no
    filesystem side-effects occur.
    """
    with (
        patch.object(svc, "_write_infra_env"),
        patch.object(svc, "_create_db_configs"),
        patch.object(svc, "_create_logging_configs"),
        patch.object(svc, "_set_base_url"),
    ):
        svc.create(**payload)


@pytest.fixture
def fernet_env():
    """Set a valid FERNET_KEY in os.environ for tests that mock _write_infra_env."""
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    old = os.environ.get("FERNET_KEY")
    os.environ["FERNET_KEY"] = key
    yield key
    if old is None:
        os.environ.pop("FERNET_KEY", None)
    else:
        os.environ["FERNET_KEY"] = old


@pytest.fixture(autouse=True)
def reset_status():
    from apps.setup import status as _status

    _status._state["status"] = "idle"
    _status._state["current_step"] = None
    _status._state["steps"] = []
    _status._state["error"] = None
    yield
    _status._state["status"] = "idle"
    _status._state["current_step"] = None
    _status._state["steps"] = []
    _status._state["error"] = None


# ---------------------------------------------------------------------------
# SetupService.create() — DB workflow
# ---------------------------------------------------------------------------


class TestSetupServiceCreateWorkflow:
    def test_admin_user_created_in_db(self):
        from apps.users.models import User

        svc = _make_service()
        _run_create(svc, _sqlite_classic_payload())
        assert User.objects.filter(email="alice@example.com").exists()

    def test_admin_user_is_superuser(self):
        from apps.users.models import User

        svc = _make_service()
        _run_create(svc, _sqlite_classic_payload())
        user = User.objects.get(email="alice@example.com")
        assert user.is_superuser is True

    def test_setup_complete_persisted_in_db(self):
        from apps.configurations.selectors import Setup

        svc = _make_service()
        _run_create(svc, _sqlite_classic_payload())
        assert Setup.get_setup_complete() is True

    def test_app_name_config_persisted(self):
        from apps.configurations.selectors import General

        svc = _make_service()
        _run_create(svc, _sqlite_classic_payload())
        assert General.get_app_name() == "TestPlanner"

    def test_auth_mode_config_persisted(self):
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth

        svc = _make_service()
        _run_create(svc, _sqlite_classic_payload())
        assert Auth.get_auth_mode() == AuthMode.CLASSIC

    def test_second_create_raises_conflict(self):
        from apps.core.exceptions import ConflictException

        svc1 = _make_service()
        _run_create(svc1, _sqlite_classic_payload())

        svc2 = _make_service()
        with pytest.raises(ConflictException):
            _run_create(svc2, _sqlite_classic_payload(email="bob@example.com"))


# ---------------------------------------------------------------------------
# SetupService — SAML auth type creates provider in DB
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("fernet_env")
class TestSetupServiceSetAuthTypeSaml:
    def _saml_payload(self):
        from cryptography.fernet import Fernet

        return {
            "admin": {
                "first_name": "Bob",
                "last_name": "Admin",
                "email": "bob@example.com",
                "password": "SecurePass123!",
            },
            "app": {
                "app_name": "SamlPlanner",
                "app_url": "https://saml.example.com",
            },
            "infra": {
                "deployment_type": "local",
                "fernet_key": Fernet.generate_key().decode(),
            },
            "db": {"engine": "sqlite"},
            "auth": {
                "auth_type": "saml",
                "provider_name": "TestIDP",
                "idp_entity_id": "https://idp.example.com/entity",
                "idp_sso_url": "https://idp.example.com/sso",
                "idp_x509_cert": "A" * 100,
                "sp_entity_id": "https://sp.example.com/entity",
                "sp_assertion_url": "https://sp.example.com/acs",
            },
            "storage": {"storage_type": "database"},
            "email": {
                "email_type": "console",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
            },
            "logging": {
                "log_destination": "local",
                "log_name": "application",
                "log_path": "/tmp/logs",  # nosec B108
            },
        }

    def test_saml_provider_created_in_db(self):
        from apps.saml.models import SAML

        svc = _make_service()
        mock_test_svc = MagicMock()
        with (
            patch.object(svc, "_test_service", return_value=mock_test_svc),
            patch.object(svc, "_write_infra_env"),
            patch.object(svc, "_create_db_configs"),
            patch.object(svc, "_create_logging_configs"),
            patch.object(svc, "_set_base_url"),
        ):
            svc.create(**self._saml_payload())

        assert SAML.objects.filter(name="TestIDP").exists()

    def test_saml_auth_mode_set_to_saml(self):
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth

        svc = _make_service()
        mock_test_svc = MagicMock()
        with (
            patch.object(svc, "_test_service", return_value=mock_test_svc),
            patch.object(svc, "_write_infra_env"),
            patch.object(svc, "_create_db_configs"),
            patch.object(svc, "_create_logging_configs"),
            patch.object(svc, "_set_base_url"),
        ):
            svc.create(**self._saml_payload())

        assert Auth.get_auth_mode() == AuthMode.SAML


# ---------------------------------------------------------------------------
# SetupService — OAuth auth type creates provider in DB
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("fernet_env")
class TestSetupServiceSetAuthTypeOauth:
    def _oauth_payload(self):
        from cryptography.fernet import Fernet

        return {
            "admin": {
                "first_name": "Charlie",
                "last_name": "Admin",
                "email": "charlie@example.com",
                "password": "SecurePass123!",
            },
            "app": {
                "app_name": "OauthPlanner",
                "app_url": "https://oauth.example.com",
            },
            "infra": {
                "deployment_type": "local",
                "fernet_key": Fernet.generate_key().decode(),
            },
            "db": {"engine": "sqlite"},
            "auth": {
                "auth_type": "oauth",
                "provider_name": "TestOAuth",
                "client_id": "my-client-id",
                "client_secret": "my-client-secret",
                "auth_endpoint": "https://idp.example.com/auth",
                "token_endpoint": "https://idp.example.com/token",
                "userinfo_endpoint": "https://idp.example.com/userinfo",
                "scope": "openid email profile",
            },
            "storage": {"storage_type": "database"},
            "email": {
                "email_type": "console",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
            },
            "logging": {
                "log_destination": "local",
                "log_name": "application",
                "log_path": "/tmp/logs",  # nosec B108
            },
        }

    def test_oauth_provider_created_in_db(self):
        from apps.oauth.models import OAuth

        svc = _make_service()
        mock_test_svc = MagicMock()
        with (
            patch.object(svc, "_test_service", return_value=mock_test_svc),
            patch.object(svc, "_write_infra_env"),
            patch.object(svc, "_create_db_configs"),
            patch.object(svc, "_create_logging_configs"),
            patch.object(svc, "_set_base_url"),
        ):
            svc.create(**self._oauth_payload())

        assert OAuth.objects.filter(name="TestOAuth").exists()

    def test_oauth_auth_mode_set_to_oauth(self):
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth

        svc = _make_service()
        mock_test_svc = MagicMock()
        with (
            patch.object(svc, "_test_service", return_value=mock_test_svc),
            patch.object(svc, "_write_infra_env"),
            patch.object(svc, "_create_db_configs"),
            patch.object(svc, "_create_logging_configs"),
            patch.object(svc, "_set_base_url"),
        ):
            svc.create(**self._oauth_payload())

        assert Auth.get_auth_mode() == AuthMode.OAUTH
