"""Unit tests for apps.setup services — all DB calls are mocked."""

import io
import os
from unittest.mock import MagicMock, patch

import pytest

from apps.core.exceptions import ConflictException, ValidationException
from apps.setup.constants import DeploymentType
from apps.setup.services import SetupService
from apps.setup.services import (
    TestService as SetupTestService,  # alias avoids pytest collection
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(cls):
    return cls(user=None, request=None)


def _sqlite_local_payload():
    """Minimal valid setup payload — sqlite + local deployment + classic auth."""
    from cryptography.fernet import Fernet

    return {
        "admin": {
            "first_name": "Alice",
            "last_name": "Admin",
            "email": "alice@example.com",
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


# ---------------------------------------------------------------------------
# SetupTestService — test_db_connection
# ---------------------------------------------------------------------------


class TestDbConnectionService:
    def test_raises_if_psycopg2_not_installed(self):
        svc = _make_service(SetupTestService)
        with patch.dict("sys.modules", {"psycopg2": None}):
            with pytest.raises(ValidationException, match="psycopg2 is not installed"):
                svc.test_db_connection(
                    host="localhost",
                    port="5432",
                    db_name="mydb",
                    user_name="admin",
                    password="secret",
                )

    def test_raises_on_connection_failure(self):
        svc = _make_service(SetupTestService)
        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.side_effect = Exception("connection refused")
        with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
            with pytest.raises(ValidationException, match="connection refused"):
                svc.test_db_connection(
                    host="localhost",
                    port="5432",
                    db_name="mydb",
                    user_name="admin",
                    password="badpass",
                )

    def test_succeeds_on_valid_connection(self):
        svc = _make_service(SetupTestService)
        mock_conn = MagicMock()
        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
            svc.test_db_connection(
                host="localhost",
                port="5432",
                db_name="mydb",
                user_name="admin",
                password="secret",
            )
        mock_conn.close.assert_called_once()

    def test_passes_correct_args_to_psycopg2(self):
        svc = _make_service(SetupTestService)
        mock_conn = MagicMock()
        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
            svc.test_db_connection(
                host="db.example.com",
                port="5433",
                db_name="production",
                user_name="dbuser",
                password="dbpass",
            )
        mock_psycopg2.connect.assert_called_once_with(
            host="db.example.com",
            port=5433,
            dbname="production",
            user="dbuser",
            password="dbpass",
            connect_timeout=5,
        )


# ---------------------------------------------------------------------------
# SetupTestService — test_email_connection
# ---------------------------------------------------------------------------


class TestEmailConnectionService:
    def test_raises_on_send_failure(self):
        svc = _make_service(SetupTestService)
        mock_sender = MagicMock()
        mock_sender.send.side_effect = Exception("SMTP auth failed")
        with patch("emailcore.EmailSender", return_value=mock_sender):
            with pytest.raises(ValidationException, match="SMTP auth failed"):
                svc.test_email_connection(
                    email_type="smtp",
                    from_address="test@example.com",
                )

    def test_succeeds_on_valid_send(self):
        svc = _make_service(SetupTestService)
        mock_sender = MagicMock()
        mock_sender.send.return_value = None
        with patch("emailcore.EmailSender", return_value=mock_sender):
            svc.test_email_connection(
                email_type="console",
                from_address="test@example.com",
            )
        mock_sender.send.assert_called_once()

    def test_send_uses_from_address_as_recipient(self):
        svc = _make_service(SetupTestService)
        mock_sender = MagicMock()
        with patch("emailcore.EmailSender", return_value=mock_sender):
            svc.test_email_connection(
                email_type="console",
                from_address="admin@example.com",
            )
        call_kwargs = mock_sender.send.call_args[1]
        assert call_kwargs["to"] == "admin@example.com"


# ---------------------------------------------------------------------------
# SetupService — create (orchestration)
# ---------------------------------------------------------------------------


class TestSetupServiceCreate:
    def test_raises_conflict_if_setup_already_complete(self):
        svc = _make_service(SetupService)
        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete",
            return_value=True,
        ):
            with pytest.raises(ConflictException):
                svc.create(**_sqlite_local_payload())

    def test_status_fail_called_on_exception(self):
        svc = _make_service(SetupService)
        with (
            patch(
                "apps.configurations.selectors.Setup.get_setup_complete",
                return_value=False,
            ),
            patch("apps.setup.status.start") as mock_start,
            patch("apps.setup.status.fail") as mock_fail,
            patch("apps.setup.status.advance"),
            patch.object(
                svc, "_write_infra_env", side_effect=Exception("env write failed")
            ),
        ):
            with pytest.raises(Exception, match="env write failed"):
                svc.create(**_sqlite_local_payload())

        mock_start.assert_called_once()
        mock_fail.assert_called_once()
        assert "env write failed" in mock_fail.call_args[0][0]

    def test_status_complete_called_on_success(self):
        svc = _make_service(SetupService)
        with (
            patch(
                "apps.configurations.selectors.Setup.get_setup_complete",
                return_value=False,
            ),
            patch("apps.setup.status.start"),
            patch("apps.setup.status.advance"),
            patch("apps.setup.status.complete") as mock_complete,
            patch("apps.setup.status.fail") as mock_fail,
            patch("apps.setup.services.transaction.atomic"),
            patch.object(svc, "_write_infra_env"),
            patch.object(svc, "_create_db_configs"),
            patch.object(svc, "_create_logging_configs"),
            patch.object(svc, "_create_admin_user"),
            patch.object(svc, "_set_app_details"),
            patch.object(svc, "_save_infra_db_configs"),
            patch.object(svc, "_set_auth_type"),
            patch.object(svc, "_save_infra_storage_configs"),
            patch.object(svc, "_save_email_configs"),
            patch.object(svc, "_mark_setup_complete"),
            patch.object(svc, "_set_base_url"),
        ):
            svc.create(**_sqlite_local_payload())

        mock_complete.assert_called_once()
        mock_fail.assert_not_called()

    def test_all_service_methods_called_in_order(self):
        svc = _make_service(SetupService)
        call_order = []

        def _recorder(name):
            def _inner(*args, **kwargs):
                call_order.append(name)

            return _inner

        with (
            patch(
                "apps.configurations.selectors.Setup.get_setup_complete",
                return_value=False,
            ),
            patch("apps.setup.status.start"),
            patch("apps.setup.status.advance"),
            patch("apps.setup.status.complete"),
            patch("apps.setup.services.transaction.atomic"),
            patch.object(
                svc, "_write_infra_env", side_effect=_recorder("write_infra_env")
            ),
            patch.object(
                svc, "_create_db_configs", side_effect=_recorder("create_db_configs")
            ),
            patch.object(
                svc,
                "_create_logging_configs",
                side_effect=_recorder("create_logging_configs"),
            ),
            patch.object(
                svc, "_create_admin_user", side_effect=_recorder("create_admin_user")
            ),
            patch.object(
                svc, "_set_app_details", side_effect=_recorder("set_app_details")
            ),
            patch.object(
                svc,
                "_save_infra_db_configs",
                side_effect=_recorder("save_infra_db_configs"),
            ),
            patch.object(svc, "_set_auth_type", side_effect=_recorder("set_auth_type")),
            patch.object(
                svc,
                "_save_infra_storage_configs",
                side_effect=_recorder("save_infra_storage_configs"),
            ),
            patch.object(
                svc, "_save_email_configs", side_effect=_recorder("save_email_configs")
            ),
            patch.object(
                svc,
                "_mark_setup_complete",
                side_effect=_recorder("mark_setup_complete"),
            ),
            patch.object(svc, "_set_base_url", side_effect=_recorder("set_base_url")),
        ):
            svc.create(**_sqlite_local_payload())

        assert call_order == [
            "write_infra_env",
            "create_db_configs",
            "create_logging_configs",
            "create_admin_user",
            "set_app_details",
            "save_infra_db_configs",
            "set_auth_type",
            "save_infra_storage_configs",
            "save_email_configs",
            "mark_setup_complete",
            "set_base_url",
        ]


# ---------------------------------------------------------------------------
# Shared helpers for cert-based tests
# ---------------------------------------------------------------------------


def _generate_test_cert_b64():
    """Return a real self-signed DER cert as base64 (no PEM headers)."""
    import base64
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc))
        .not_valid_after(datetime.datetime(2099, 1, 1, tzinfo=datetime.timezone.utc))
        .sign(key, hashes.SHA256())
    )
    return base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode()


def urllib_http_error(code, body_bytes):
    import urllib.error

    return urllib.error.HTTPError(
        url=None, code=code, msg="", hdrs=None, fp=io.BytesIO(body_bytes)
    )


# ---------------------------------------------------------------------------
# SetupService — _save_infra_storage_configs
# ---------------------------------------------------------------------------


class TestSaveInfraStorageConfigs:
    def test_filesystem_creates_storage_directory(self, tmp_path):
        svc = _make_service(SetupService)
        target = str(tmp_path / "media" / "uploads")
        with patch.object(svc, "_config_service", return_value=MagicMock()):
            svc._save_infra_storage_configs(
                storage={"storage_type": "filesystem", "storage_path": target}
            )
        assert os.path.isdir(target)

    def test_filesystem_creation_idempotent_when_directory_exists(self, tmp_path):
        svc = _make_service(SetupService)
        target = str(tmp_path / "existing")
        os.makedirs(target)
        with patch.object(svc, "_config_service", return_value=MagicMock()):
            svc._save_infra_storage_configs(
                storage={"storage_type": "filesystem", "storage_path": target}
            )
        assert os.path.isdir(target)

    def test_filesystem_creation_failure_propagates(self):
        svc = _make_service(SetupService)
        with (
            patch.object(svc, "_config_service", return_value=MagicMock()),
            patch("os.makedirs", side_effect=OSError("Permission denied")),
        ):
            with pytest.raises(OSError, match="Permission denied"):
                svc._save_infra_storage_configs(
                    storage={
                        "storage_type": "filesystem",
                        "storage_path": "/no-perms/path",
                    }
                )

    def test_filesystem_saves_storage_path_config(self, tmp_path):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with patch.object(svc, "_config_service", return_value=mock_cfg):
            svc._save_infra_storage_configs(
                storage={"storage_type": "filesystem", "storage_path": str(tmp_path)}
            )
        mock_cfg.set_config.assert_any_call(
            config_code="STORAGE_PATH", value=str(tmp_path)
        )

    def test_s3_does_not_create_local_directory(self, tmp_path):
        svc = _make_service(SetupService)
        absent = str(tmp_path / "should_not_exist")
        with patch.object(svc, "_config_service", return_value=MagicMock()):
            svc._save_infra_storage_configs(
                storage={"storage_type": "s3", "storage_path": "arn:aws:s3:::my-bucket"}
            )
        assert not os.path.isdir(absent)

    def test_s3_saves_storage_path_config(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with patch.object(svc, "_config_service", return_value=mock_cfg):
            svc._save_infra_storage_configs(
                storage={"storage_type": "s3", "storage_path": "arn:aws:s3:::my-bucket"}
            )
        mock_cfg.set_config.assert_any_call(
            config_code="STORAGE_PATH", value="arn:aws:s3:::my-bucket"
        )

    def test_database_does_not_save_storage_path_config(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with patch.object(svc, "_config_service", return_value=mock_cfg):
            svc._save_infra_storage_configs(storage={"storage_type": "database"})
        saved_codes = [
            call.kwargs.get("config_code")
            for call in mock_cfg.set_config.call_args_list
        ]
        assert "STORAGE_PATH" not in saved_codes

    def test_database_saves_storage_type_config(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with patch.object(svc, "_config_service", return_value=mock_cfg):
            svc._save_infra_storage_configs(storage={"storage_type": "database"})
        mock_cfg.set_config.assert_any_call(
            config_code="STORAGE_TYPE", value="database"
        )


# ---------------------------------------------------------------------------
# SetupTestService — test_saml_connection
# ---------------------------------------------------------------------------


class TestSAMLConnectionService:
    def test_raises_on_invalid_cert(self):
        svc = _make_service(SetupTestService)
        with pytest.raises(ValidationException, match="Invalid X.509 certificate"):
            svc.test_saml_connection(
                idp_sso_url="https://idp.example.com/sso",
                idp_x509_cert="AAAA",  # valid base64, not valid DER
            )

    def test_raises_on_expired_cert(self):
        import datetime

        svc = _make_service(SetupTestService)
        mock_cert = MagicMock()
        mock_cert.not_valid_after_utc = datetime.datetime(
            2000, 1, 1, tzinfo=datetime.timezone.utc
        )
        with (
            patch(
                "cryptography.x509.load_der_x509_certificate", return_value=mock_cert
            ),
            pytest.raises(ValidationException, match="expired"),
        ):
            svc.test_saml_connection(
                idp_sso_url="https://idp.example.com/sso",
                idp_x509_cert=_generate_test_cert_b64(),
            )

    def test_raises_on_unreachable_sso_url(self):
        import urllib.error

        svc = _make_service(SetupTestService)
        cert_b64 = _generate_test_cert_b64()
        with (
            patch(
                "urllib.request.urlopen",
                side_effect=urllib.error.URLError("Name not resolved"),
            ),
            pytest.raises(ValidationException, match="Cannot reach IdP SSO URL"),
        ):
            svc.test_saml_connection(
                idp_sso_url="https://unreachable.example.com/sso",
                idp_x509_cert=cert_b64,
            )

    def test_succeeds_when_idp_returns_http_error(self):
        """Any HTTP response (e.g. 302) confirms the endpoint is reachable."""
        import urllib.error

        svc = _make_service(SetupTestService)
        cert_b64 = _generate_test_cert_b64()
        http_err = urllib.error.HTTPError(
            url=None, code=302, msg="Found", hdrs=None, fp=None
        )
        with patch("urllib.request.urlopen", side_effect=http_err):
            svc.test_saml_connection(
                idp_sso_url="https://idp.example.com/sso",
                idp_x509_cert=cert_b64,
            )

    def test_raises_validation_exception_on_generic_error(self):
        """Non-URL exceptions from urlopen are wrapped in ValidationException."""
        svc = _make_service(SetupTestService)
        cert_b64 = _generate_test_cert_b64()
        with (
            patch(
                "urllib.request.urlopen",
                side_effect=ConnectionError("unexpected error"),
            ),
            pytest.raises(ValidationException, match="unexpected error"),
        ):
            svc.test_saml_connection(
                idp_sso_url="https://idp.example.com/sso",
                idp_x509_cert=cert_b64,
            )


# ---------------------------------------------------------------------------
# SetupTestService — test_oauth_connection
# ---------------------------------------------------------------------------


class TestOAuthConnectionService:
    def test_raises_on_invalid_client_credentials(self):
        svc = _make_service(SetupTestService)
        err = urllib_http_error(401, b'{"error": "invalid_client"}')
        with (
            patch("urllib.request.urlopen", side_effect=err),
            pytest.raises(
                ValidationException, match="client credentials were rejected"
            ),
        ):
            svc.test_oauth_connection(
                client_id="bad-id",
                client_secret="bad-secret",
                auth_endpoint="https://idp.example.com/auth",
                token_endpoint="https://idp.example.com/token",
            )

    def test_raises_on_unreachable_token_endpoint(self):
        import urllib.error

        svc = _make_service(SetupTestService)
        with (
            patch(
                "urllib.request.urlopen", side_effect=urllib.error.URLError("refused")
            ),
            pytest.raises(ValidationException, match="Cannot reach token endpoint"),
        ):
            svc.test_oauth_connection(
                client_id="cid",
                client_secret="csecret",
                auth_endpoint="https://idp.example.com/auth",
                token_endpoint="https://unreachable.example.com/token",
            )

    def test_raises_on_unreachable_auth_endpoint(self):
        import urllib.error

        svc = _make_service(SetupTestService)
        token_err = urllib_http_error(400, b'{"error": "invalid_grant"}')
        auth_err = urllib.error.URLError("refused")
        with (
            patch("urllib.request.urlopen", side_effect=[token_err, auth_err]),
            pytest.raises(
                ValidationException, match="Cannot reach authorisation endpoint"
            ),
        ):
            svc.test_oauth_connection(
                client_id="cid",
                client_secret="csecret",
                auth_endpoint="https://unreachable.example.com/auth",
                token_endpoint="https://idp.example.com/token",
            )

    def test_succeeds_when_token_endpoint_returns_invalid_grant(self):
        """
        invalid_grant means credentials were accepted — endpoint and creds are valid.
        """
        svc = _make_service(SetupTestService)
        token_err = urllib_http_error(400, b'{"error": "invalid_grant"}')
        auth_mock = MagicMock()
        with patch("urllib.request.urlopen", side_effect=[token_err, auth_mock]):
            svc.test_oauth_connection(
                client_id="valid-id",
                client_secret="valid-secret",
                auth_endpoint="https://idp.example.com/auth",
                token_endpoint="https://idp.example.com/token",
            )

    def test_raises_validation_exception_on_generic_token_error(self):
        """
        Non-URL exceptions on the token request are wrapped in ValidationException.
        """
        svc = _make_service(SetupTestService)
        with (
            patch(
                "urllib.request.urlopen",
                side_effect=ConnectionError("network unreachable"),
            ),
            pytest.raises(ValidationException, match="network unreachable"),
        ):
            svc.test_oauth_connection(
                client_id="cid",
                client_secret="csecret",
                auth_endpoint="https://idp.example.com/auth",
                token_endpoint="https://idp.example.com/token",
            )


# ---------------------------------------------------------------------------
# SetupService — _write_infra_env (local deployment)
# ---------------------------------------------------------------------------


class TestWriteInfraEnvLocal:
    def test_writes_fernet_key_to_dotenv(self):
        svc = _make_service(SetupService)
        mock_env = MagicMock()
        with patch("pycore.DotEnv", return_value=mock_env):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.LOCAL,
                    fernet_key="test-fernet-key",
                )
        mock_env.write.assert_any_call("FERNET_KEY", "test-fernet-key")

    def test_writes_fernet_key_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.LOCAL,
                    fernet_key="test-fernet-key",
                )
                assert os.environ["FERNET_KEY"] == "test-fernet-key"

    def test_writes_empty_secrets_prefix_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.LOCAL,
                    fernet_key="key",
                )
                assert os.environ["SECRETS_PREFIX"] == ""

    def test_writes_db_password_source_env_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.LOCAL,
                    fernet_key="key",
                )
                assert os.environ["DB_PASSWORD_SOURCE"] == "env"

    def test_pops_db_secret_name_from_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {"DB_SECRET_NAME": "old-value"}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.LOCAL,
                    fernet_key="key",
                )
                assert "DB_SECRET_NAME" not in os.environ

    def test_does_not_write_aws_region_for_local(self):
        svc = _make_service(SetupService)
        mock_env = MagicMock()
        with patch("pycore.DotEnv", return_value=mock_env):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.LOCAL,
                    fernet_key="key",
                )
        written_keys = [call.args[0] for call in mock_env.write.call_args_list]
        assert "AWS_REGION" not in written_keys


# ---------------------------------------------------------------------------
# SetupService — _write_infra_env (AWS deployment)
# ---------------------------------------------------------------------------


class TestWriteInfraEnvAws:
    def test_strips_trailing_slash_from_secrets_prefix(self):
        svc = _make_service(SetupService)
        mock_env = MagicMock()
        with patch("pycore.DotEnv", return_value=mock_env):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.AWS,
                    aws_region="eu-west-1",
                    secrets_prefix="prod/",
                    aws_auth_mode="role",
                )
        mock_env.write.assert_any_call("SECRETS_PREFIX", "prod")

    def test_writes_db_secret_name_derived_from_prefix(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.AWS,
                    aws_region="eu-west-1",
                    secrets_prefix="myapp/prod",
                    aws_auth_mode="role",
                )
                assert os.environ["DB_SECRET_NAME"] == "myapp/prod/db"

    def test_writes_aws_region_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.AWS,
                    aws_region="us-east-1",
                    secrets_prefix="prefix",
                    aws_auth_mode="role",
                )
                assert os.environ["AWS_REGION"] == "us-east-1"
                assert os.environ["AWS_DEFAULT_REGION"] == "us-east-1"

    def test_writes_db_password_source_aws(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.AWS,
                    aws_region="eu-west-1",
                    secrets_prefix="prefix",
                    aws_auth_mode="role",
                )
                assert os.environ["DB_PASSWORD_SOURCE"] == "aws"

    def test_role_auth_does_not_write_access_key_to_dotenv(self):
        svc = _make_service(SetupService)
        mock_env = MagicMock()
        with patch("pycore.DotEnv", return_value=mock_env):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.AWS,
                    aws_region="eu-west-1",
                    secrets_prefix="prefix",
                    aws_auth_mode="role",
                )
        written_keys = [call.args[0] for call in mock_env.write.call_args_list]
        assert "AWS_ACCESS_KEY_ID" not in written_keys

    def test_user_auth_writes_access_key_to_dotenv(self):
        svc = _make_service(SetupService)
        mock_env = MagicMock()
        with patch("pycore.DotEnv", return_value=mock_env):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.AWS,
                    aws_region="eu-west-1",
                    secrets_prefix="prefix",
                    aws_auth_mode="user",
                    aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
                    aws_secret_access_key="secret",
                )
        mock_env.write.assert_any_call("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")

    def test_user_auth_writes_access_key_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.AWS,
                    aws_region="eu-west-1",
                    secrets_prefix="prefix",
                    aws_auth_mode="user",
                    aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
                    aws_secret_access_key="secret",
                )
                assert os.environ["AWS_ACCESS_KEY_ID"] == "AKIAIOSFODNN7EXAMPLE"

    def test_user_auth_writes_secret_access_key_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._write_infra_env(
                    deployment_type=DeploymentType.AWS,
                    aws_region="eu-west-1",
                    secrets_prefix="prefix",
                    aws_auth_mode="user",
                    aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
                    aws_secret_access_key="wJalrXUtnFEMI/K7MDENG",
                )
                assert os.environ["AWS_SECRET_ACCESS_KEY"] == "wJalrXUtnFEMI/K7MDENG"


# ---------------------------------------------------------------------------
# SetupService — _create_logging_configs
# ---------------------------------------------------------------------------


class TestCreateLoggingConfigs:
    def test_writes_log_destination_to_dotenv(self):
        svc = _make_service(SetupService)
        mock_env = MagicMock()
        with patch("pycore.DotEnv", return_value=mock_env):
            with patch.dict(os.environ, {}, clear=False):
                svc._create_logging_configs(
                    log_destination="local",
                    log_name="app",
                    log_path="/tmp/logs",  # nosec B108
                )
        mock_env.write.assert_any_call("LOG_DESTINATION", "local")

    def test_writes_log_destination_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._create_logging_configs(
                    log_destination="cloudwatch",
                    log_name="app",
                )
                assert os.environ["LOG_DESTINATION"] == "cloudwatch"

    def test_writes_log_name_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._create_logging_configs(
                    log_destination="local",
                    log_name="my-app",
                    log_path="/tmp/logs",  # nosec B108
                )
                assert os.environ["LOG_NAME"] == "my-app"

    def test_writes_log_path_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._create_logging_configs(
                    log_destination="local",
                    log_name="app",
                    log_path="/var/log/app",
                )
                assert os.environ["LOG_PATH"] == "/var/log/app"

    def test_writes_empty_log_path_when_none(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._create_logging_configs(
                    log_destination="cloudwatch",
                    log_name="app",
                    log_path=None,
                )
                assert os.environ["LOG_PATH"] == ""

    def test_writes_log_rotation_to_os_environ(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._create_logging_configs(
                    log_destination="local",
                    log_name="app",
                    log_path="/tmp/logs",  # nosec B108
                    log_rotation="size",
                )
                assert os.environ["LOG_ROTATION"] == "size"

    def test_writes_default_rotation_size_mb_when_none(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._create_logging_configs(
                    log_destination="local",
                    log_name="app",
                    log_path="/tmp/logs",  # nosec B108
                    log_rotation_size_mb=None,
                )
                assert os.environ["LOG_ROTATION_SIZE_MB"] == "10"

    def test_writes_empty_s3_bucket_when_none(self):
        svc = _make_service(SetupService)
        with patch("pycore.DotEnv", return_value=MagicMock()):
            with patch.dict(os.environ, {}, clear=False):
                svc._create_logging_configs(
                    log_destination="local",
                    log_name="app",
                    log_path="/tmp/logs",  # nosec B108
                    log_s3_bucket=None,
                )
                assert os.environ["LOG_S3_BUCKET"] == ""


# ---------------------------------------------------------------------------
# SetupService — _save_email_configs
# ---------------------------------------------------------------------------


class TestSaveEmailConfigs:
    def test_console_saves_email_type(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with patch.object(svc, "_config_service", return_value=mock_cfg):
            svc._save_email_configs(
                email_data={
                    "email_type": "console",
                    "from_address": "noreply@example.com",
                    "from_name": "Test",
                }
            )
        mock_cfg.set_config.assert_any_call(config_code="EMAIL_TYPE", value="console")

    def test_console_saves_from_address(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with patch.object(svc, "_config_service", return_value=mock_cfg):
            svc._save_email_configs(
                email_data={
                    "email_type": "console",
                    "from_address": "sender@example.com",
                    "from_name": "Test",
                }
            )
        mock_cfg.set_config.assert_any_call(
            config_code="EMAIL_FROM_ADDRESS", value="sender@example.com"
        )

    def test_console_saves_from_name(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with patch.object(svc, "_config_service", return_value=mock_cfg):
            svc._save_email_configs(
                email_data={
                    "email_type": "console",
                    "from_address": "noreply@example.com",
                    "from_name": "MyApp",
                }
            )
        mock_cfg.set_config.assert_any_call(
            config_code="EMAIL_FROM_NAME", value="MyApp"
        )

    def test_console_does_not_call_test_email_connection(self):
        svc = _make_service(SetupService)
        mock_test = MagicMock()
        with (
            patch.object(svc, "_config_service", return_value=MagicMock()),
            patch.object(svc, "_test_service", return_value=mock_test),
        ):
            svc._save_email_configs(
                email_data={
                    "email_type": "console",
                    "from_address": "noreply@example.com",
                    "from_name": "Test",
                }
            )
        mock_test.test_email_connection.assert_not_called()

    def test_smtp_calls_test_email_connection(self):
        svc = _make_service(SetupService)
        mock_test = MagicMock()
        with (
            patch.object(svc, "_config_service", return_value=MagicMock()),
            patch.object(svc, "_test_service", return_value=mock_test),
        ):
            svc._save_email_configs(
                email_data={
                    "email_type": "smtp",
                    "from_address": "noreply@example.com",
                    "from_name": "Test",
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "smtp_enc_type": "starttls",
                }
            )
        mock_test.test_email_connection.assert_called_once()

    def test_smtp_saves_smtp_host(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with (
            patch.object(svc, "_config_service", return_value=mock_cfg),
            patch.object(svc, "_test_service", return_value=MagicMock()),
        ):
            svc._save_email_configs(
                email_data={
                    "email_type": "smtp",
                    "from_address": "noreply@example.com",
                    "from_name": "Test",
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "smtp_enc_type": "starttls",
                }
            )
        mock_cfg.set_config.assert_any_call(
            config_code="EMAIL_SMTP_HOST", value="smtp.example.com"
        )

    def test_smtp_saves_smtp_port(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with (
            patch.object(svc, "_config_service", return_value=mock_cfg),
            patch.object(svc, "_test_service", return_value=MagicMock()),
        ):
            svc._save_email_configs(
                email_data={
                    "email_type": "smtp",
                    "from_address": "noreply@example.com",
                    "from_name": "Test",
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 465,
                    "smtp_enc_type": "ssl",
                }
            )
        mock_cfg.set_config.assert_any_call(config_code="EMAIL_SMTP_PORT", value=465)

    def test_smtp_with_auth_saves_username(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with (
            patch.object(svc, "_config_service", return_value=mock_cfg),
            patch.object(svc, "_test_service", return_value=MagicMock()),
        ):
            svc._save_email_configs(
                email_data={
                    "email_type": "smtp",
                    "from_address": "noreply@example.com",
                    "from_name": "Test",
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "smtp_enc_type": "starttls",
                    "smtp_auth_enabled": True,
                    "smtp_username": "smtpuser",
                    "smtp_password": "smtppass",
                }
            )
        mock_cfg.set_config.assert_any_call(
            config_code="EMAIL_SMTP_USERNAME", value="smtpuser"
        )

    def test_smtp_without_auth_does_not_save_credentials(self):
        svc = _make_service(SetupService)
        mock_cfg = MagicMock()
        with (
            patch.object(svc, "_config_service", return_value=mock_cfg),
            patch.object(svc, "_test_service", return_value=MagicMock()),
        ):
            svc._save_email_configs(
                email_data={
                    "email_type": "smtp",
                    "from_address": "noreply@example.com",
                    "from_name": "Test",
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "smtp_enc_type": "starttls",
                    "smtp_auth_enabled": False,
                }
            )
        saved_codes = [
            call.kwargs.get("config_code")
            for call in mock_cfg.set_config.call_args_list
        ]
        assert "EMAIL_SMTP_USERNAME" not in saved_codes
        assert "EMAIL_SMTP_PASSWORD" not in saved_codes
