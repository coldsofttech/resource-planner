from apps.setup.serializers import (
    AdminInputSerializer,
    AppInputSerializer,
    AuthenticationInputSerializer,
    DatabaseInputSerializer,
    DbTestInputSerializer,
    EmailInputSerializer,
    EmailTestInputSerializer,
    InfrastructureInputSerializer,
    LoggingInputSerializer,
    SetupInputSerializer,
    StorageInputSerializer,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid(serializer_class, data):
    s = serializer_class(data=data)
    assert s.is_valid(), s.errors
    return s.validated_data


def _errors(serializer_class, data):
    s = serializer_class(data=data)
    assert not s.is_valid()
    return s.errors


def _valid_fernet_key():
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode()


def _valid_x509_body():
    return "A" * 100


def _valid_setup_payload(overrides=None):
    payload = {
        "admin": {
            "first_name": "Alice",
            "last_name": "Admin",
            "email": "alice@example.com",
            "password": "SecurePass123!",
        },
        "app": {
            "app_name": "MyPlanner",
            "app_url": "https://planner.example.com",
        },
        "infra": {
            "deployment_type": "local",
            "fernet_key": _valid_fernet_key(),
        },
        "db": {
            "engine": "sqlite",
        },
        "auth": {
            "auth_type": "classic",
            "self_register": True,
        },
        "storage": {
            "storage_type": "database",
        },
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
    if overrides:
        payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# AdminInputSerializer
# ---------------------------------------------------------------------------


class TestAdminInputSerializer:
    def test_valid_payload_passes(self):
        data = _valid(
            AdminInputSerializer,
            {
                "first_name": "Alice",
                "last_name": "Admin",
                "email": "alice@example.com",
                "password": "SecurePass123!",
            },
        )
        assert data["email"] == "alice@example.com"

    def test_missing_first_name_fails(self):
        errors = _errors(
            AdminInputSerializer,
            {
                "last_name": "Admin",
                "email": "alice@example.com",
                "password": "SecurePass123!",
            },
        )
        assert "first_name" in errors

    def test_missing_last_name_fails(self):
        errors = _errors(
            AdminInputSerializer,
            {
                "first_name": "Alice",
                "email": "alice@example.com",
                "password": "SecurePass123!",
            },
        )
        assert "last_name" in errors

    def test_missing_email_fails(self):
        errors = _errors(
            AdminInputSerializer,
            {
                "first_name": "Alice",
                "last_name": "Admin",
                "password": "SecurePass123!",
            },
        )
        assert "email" in errors

    def test_invalid_email_fails(self):
        errors = _errors(
            AdminInputSerializer,
            {
                "first_name": "Alice",
                "last_name": "Admin",
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )
        assert "email" in errors

    def test_weak_password_fails(self):
        errors = _errors(
            AdminInputSerializer,
            {
                "first_name": "Alice",
                "last_name": "Admin",
                "email": "alice@example.com",
                "password": "123",
            },
        )
        assert "password" in errors

    def test_missing_password_fails(self):
        errors = _errors(
            AdminInputSerializer,
            {
                "first_name": "Alice",
                "last_name": "Admin",
                "email": "alice@example.com",
            },
        )
        assert "password" in errors


# ---------------------------------------------------------------------------
# AppInputSerializer
# ---------------------------------------------------------------------------


class TestAppInputSerializer:
    def test_valid_payload_passes(self):
        data = _valid(
            AppInputSerializer,
            {
                "app_name": "MyApp",
                "app_url": "https://app.example.com",
            },
        )
        assert data["app_name"] == "MyApp"

    def test_missing_app_url_fails(self):
        errors = _errors(AppInputSerializer, {"app_name": "MyApp"})
        assert "app_url" in errors

    def test_invalid_url_fails(self):
        errors = _errors(
            AppInputSerializer,
            {
                "app_name": "MyApp",
                "app_url": "not-a-url",
            },
        )
        assert "app_url" in errors

    def test_missing_app_name_fails(self):
        errors = _errors(
            AppInputSerializer,
            {
                "app_url": "https://app.example.com",
            },
        )
        assert "app_name" in errors

    def test_app_name_too_long_fails(self):
        errors = _errors(
            AppInputSerializer,
            {
                "app_name": "X" * 51,
                "app_url": "https://app.example.com",
            },
        )
        assert "app_name" in errors


# ---------------------------------------------------------------------------
# InfrastructureInputSerializer
# ---------------------------------------------------------------------------


class TestInfrastructureInputSerializer:
    def test_local_with_valid_fernet_key_passes(self):
        data = _valid(
            InfrastructureInputSerializer,
            {
                "deployment_type": "local",
                "fernet_key": _valid_fernet_key(),
            },
        )
        assert data["deployment_type"] == "local"

    def test_local_missing_fernet_key_fails(self):
        errors = _errors(
            InfrastructureInputSerializer,
            {
                "deployment_type": "local",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_local_with_invalid_fernet_key_fails(self):
        errors = _errors(
            InfrastructureInputSerializer,
            {
                "deployment_type": "local",
                "fernet_key": "not-a-valid-fernet-key",
            },
        )
        assert "fernet_key" in errors

    def test_aws_role_auth_passes(self):
        data = _valid(
            InfrastructureInputSerializer,
            {
                "deployment_type": "aws",
                "aws_region": "eu-west-1",
                "secrets_prefix": "myapp/prod",
                "aws_auth_mode": "role",
            },
        )
        assert data["deployment_type"] == "aws"
        assert data["aws_auth_mode"] == "role"

    def test_aws_user_auth_with_credentials_passes(self):
        data = _valid(
            InfrastructureInputSerializer,
            {
                "deployment_type": "aws",
                "aws_region": "us-east-1",
                "secrets_prefix": "myapp/prod",
                "aws_auth_mode": "user",
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            },
        )
        assert data["aws_auth_mode"] == "user"

    def test_aws_missing_region_fails(self):
        errors = _errors(
            InfrastructureInputSerializer,
            {
                "deployment_type": "aws",
                "secrets_prefix": "myapp/prod",
                "aws_auth_mode": "role",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_aws_missing_secrets_prefix_fails(self):
        errors = _errors(
            InfrastructureInputSerializer,
            {
                "deployment_type": "aws",
                "aws_region": "eu-west-1",
                "aws_auth_mode": "role",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_aws_user_auth_missing_access_key_fails(self):
        errors = _errors(
            InfrastructureInputSerializer,
            {
                "deployment_type": "aws",
                "aws_region": "eu-west-1",
                "secrets_prefix": "myapp/prod",
                "aws_auth_mode": "user",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_invalid_aws_region_format_fails(self):
        errors = _errors(
            InfrastructureInputSerializer,
            {
                "deployment_type": "aws",
                "aws_region": "US-EAST-1",
                "secrets_prefix": "myapp/prod",
                "aws_auth_mode": "role",
            },
        )
        assert "aws_region" in errors

    def test_invalid_aws_access_key_id_fails(self):
        errors = _errors(
            InfrastructureInputSerializer,
            {
                "deployment_type": "aws",
                "aws_region": "us-east-1",
                "secrets_prefix": "myapp/prod",
                "aws_auth_mode": "user",
                "aws_access_key_id": "tooshort",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            },
        )
        assert "aws_access_key_id" in errors

    def test_invalid_aws_secret_access_key_fails(self):
        errors = _errors(
            InfrastructureInputSerializer,
            {
                "deployment_type": "aws",
                "aws_region": "us-east-1",
                "secrets_prefix": "myapp/prod",
                "aws_auth_mode": "user",
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "bad!key",
            },
        )
        assert "aws_secret_access_key" in errors

    def test_invalid_deployment_type_fails(self):
        errors = _errors(
            InfrastructureInputSerializer,
            {
                "deployment_type": "azure",
            },
        )
        assert "deployment_type" in errors


# ---------------------------------------------------------------------------
# DatabaseInputSerializer
# ---------------------------------------------------------------------------


class TestDatabaseInputSerializer:
    def test_sqlite_passes_without_connection_fields(self):
        data = _valid(DatabaseInputSerializer, {"engine": "sqlite"})
        assert data["engine"] == "sqlite"

    def test_postgresql_with_all_fields_passes(self):
        data = _valid(
            DatabaseInputSerializer,
            {
                "engine": "postgresql",
                "host": "localhost",
                "port": "5432",
                "db_name": "mydb",
                "user_name": "admin",
                "password": "secret",
            },
        )
        assert data["engine"] == "postgresql"

    def test_postgresql_missing_host_fails(self):
        errors = _errors(
            DatabaseInputSerializer,
            {
                "engine": "postgresql",
                "port": "5432",
                "db_name": "mydb",
                "user_name": "admin",
                "password": "secret",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_postgresql_missing_password_fails(self):
        errors = _errors(
            DatabaseInputSerializer,
            {
                "engine": "postgresql",
                "host": "localhost",
                "port": "5432",
                "db_name": "mydb",
                "user_name": "admin",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_invalid_engine_fails(self):
        errors = _errors(DatabaseInputSerializer, {"engine": "mysql"})
        assert "engine" in errors

    def test_missing_engine_fails(self):
        errors = _errors(DatabaseInputSerializer, {})
        assert "engine" in errors


# ---------------------------------------------------------------------------
# StorageInputSerializer
# ---------------------------------------------------------------------------


class TestStorageInputSerializer:
    def test_database_type_passes_without_path(self):
        data = _valid(StorageInputSerializer, {"storage_type": "database"})
        assert data["storage_type"] == "database"

    def test_filesystem_with_path_passes(self):
        data = _valid(
            StorageInputSerializer,
            {
                "storage_type": "filesystem",
                "storage_path": "/var/media",
            },
        )
        assert data["storage_path"] == "/var/media"

    def test_filesystem_missing_path_fails(self):
        errors = _errors(StorageInputSerializer, {"storage_type": "filesystem"})
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_s3_with_valid_arn_passes(self):
        data = _valid(
            StorageInputSerializer,
            {
                "storage_type": "s3",
                "storage_path": "arn:aws:s3:::my-bucket",
            },
        )
        assert data["storage_type"] == "s3"

    def test_s3_with_invalid_arn_fails(self):
        errors = _errors(
            StorageInputSerializer,
            {
                "storage_type": "s3",
                "storage_path": "not-an-arn",
            },
        )
        assert "non_field_errors" in errors or "storage_path" in str(errors)

    def test_s3_missing_storage_path_fails(self):
        errors = _errors(StorageInputSerializer, {"storage_type": "s3"})
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_invalid_storage_type_fails(self):
        errors = _errors(StorageInputSerializer, {"storage_type": "ftp"})
        assert "storage_type" in errors


# ---------------------------------------------------------------------------
# AuthenticationInputSerializer
# ---------------------------------------------------------------------------


class TestAuthenticationInputSerializer:
    def test_classic_with_self_register_passes(self):
        data = _valid(
            AuthenticationInputSerializer,
            {
                "auth_type": "classic",
                "self_register": True,
            },
        )
        assert data["auth_type"] == "classic"

    def test_classic_missing_self_register_fails(self):
        errors = _errors(AuthenticationInputSerializer, {"auth_type": "classic"})
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_saml_with_all_fields_passes(self):
        data = _valid(
            AuthenticationInputSerializer,
            {
                "auth_type": "saml",
                "provider_name": "MyIDP",
                "idp_entity_id": "https://idp.example.com/entity",
                "idp_sso_url": "https://idp.example.com/sso",
                "idp_x509_cert": _valid_x509_body(),
                "sp_entity_id": "https://sp.example.com/entity",
                "sp_assertion_url": "https://sp.example.com/acs",
            },
        )
        assert data["auth_type"] == "saml"

    def test_saml_missing_idp_entity_id_fails(self):
        errors = _errors(
            AuthenticationInputSerializer,
            {
                "auth_type": "saml",
                "provider_name": "MyIDP",
                "idp_sso_url": "https://idp.example.com/sso",
                "idp_x509_cert": _valid_x509_body(),
                "sp_assertion_url": "https://sp.example.com/acs",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_saml_missing_idp_x509_cert_fails(self):
        errors = _errors(
            AuthenticationInputSerializer,
            {
                "auth_type": "saml",
                "provider_name": "MyIDP",
                "idp_entity_id": "https://idp.example.com/entity",
                "idp_sso_url": "https://idp.example.com/sso",
                "sp_assertion_url": "https://sp.example.com/acs",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_saml_cert_with_pem_headers_fails(self):
        pem_cert = "-----BEGIN CERTIFICATE-----\nABCDEFGH\n-----END CERTIFICATE-----"
        errors = _errors(
            AuthenticationInputSerializer,
            {
                "auth_type": "saml",
                "provider_name": "MyIDP",
                "idp_entity_id": "https://idp.example.com/entity",
                "idp_sso_url": "https://idp.example.com/sso",
                "idp_x509_cert": pem_cert,
                "sp_assertion_url": "https://sp.example.com/acs",
            },
        )
        assert "idp_x509_cert" in errors

    def test_oauth_with_all_fields_passes(self):
        data = _valid(
            AuthenticationInputSerializer,
            {
                "auth_type": "oauth",
                "provider_name": "MyOAuth",
                "client_id": "my-client-id",
                "client_secret": "my-client-secret",
                "auth_endpoint": "https://oauth.example.com/authorize",
                "token_endpoint": "https://oauth.example.com/token",
                "userinfo_endpoint": "https://oauth.example.com/userinfo",
                "scope": "openid profile email",
            },
        )
        assert data["auth_type"] == "oauth"

    def test_oauth_missing_client_id_fails(self):
        errors = _errors(
            AuthenticationInputSerializer,
            {
                "auth_type": "oauth",
                "provider_name": "MyOAuth",
                "client_secret": "my-client-secret",
                "auth_endpoint": "https://oauth.example.com/authorize",
                "token_endpoint": "https://oauth.example.com/token",
                "userinfo_endpoint": "https://oauth.example.com/userinfo",
                "scope": "openid",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_oauth_missing_scope_fails(self):
        errors = _errors(
            AuthenticationInputSerializer,
            {
                "auth_type": "oauth",
                "provider_name": "MyOAuth",
                "client_id": "my-client-id",
                "client_secret": "my-client-secret",
                "auth_endpoint": "https://oauth.example.com/authorize",
                "token_endpoint": "https://oauth.example.com/token",
                "userinfo_endpoint": "https://oauth.example.com/userinfo",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_invalid_auth_type_fails(self):
        errors = _errors(AuthenticationInputSerializer, {"auth_type": "ldap"})
        assert "auth_type" in errors


# ---------------------------------------------------------------------------
# LoggingInputSerializer
# ---------------------------------------------------------------------------


class TestLoggingInputSerializer:
    def test_local_with_log_path_passes(self):
        data = _valid(
            LoggingInputSerializer,
            {
                "log_destination": "local",
                "log_name": "app",
                "log_path": "/var/log/app",
            },
        )
        assert data["log_destination"] == "local"

    def test_local_missing_log_path_fails(self):
        errors = _errors(
            LoggingInputSerializer,
            {
                "log_destination": "local",
                "log_name": "app",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_s3_with_valid_bucket_arn_passes(self):
        data = _valid(
            LoggingInputSerializer,
            {
                "log_destination": "s3",
                "log_name": "app",
                "log_s3_bucket": "arn:aws:s3:::my-log-bucket",
            },
        )
        assert data["log_destination"] == "s3"

    def test_s3_missing_bucket_fails(self):
        errors = _errors(
            LoggingInputSerializer,
            {
                "log_destination": "s3",
                "log_name": "app",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_s3_invalid_bucket_arn_fails(self):
        errors = _errors(
            LoggingInputSerializer,
            {
                "log_destination": "s3",
                "log_name": "app",
                "log_s3_bucket": "not-an-arn",
            },
        )
        assert "log_s3_bucket" in errors

    def test_cloudwatch_passes_without_path_or_bucket(self):
        data = _valid(
            LoggingInputSerializer,
            {
                "log_destination": "cloudwatch",
                "log_name": "app",
            },
        )
        assert data["log_destination"] == "cloudwatch"

    def test_size_rotation_with_size_mb_passes(self):
        data = _valid(
            LoggingInputSerializer,
            {
                "log_destination": "local",
                "log_name": "app",
                "log_path": "/var/log",
                "log_rotation": "size",
                "log_rotation_size_mb": 50,
            },
        )
        assert data["log_rotation_size_mb"] == 50

    def test_size_rotation_missing_size_mb_fails(self):
        errors = _errors(
            LoggingInputSerializer,
            {
                "log_destination": "local",
                "log_name": "app",
                "log_path": "/var/log",
                "log_rotation": "size",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_log_rotation_size_mb_below_minimum_fails(self):
        errors = _errors(
            LoggingInputSerializer,
            {
                "log_destination": "local",
                "log_name": "app",
                "log_path": "/var/log",
                "log_rotation": "size",
                "log_rotation_size_mb": 0,
            },
        )
        assert "log_rotation_size_mb" in errors

    def test_invalid_log_destination_fails(self):
        errors = _errors(
            LoggingInputSerializer,
            {
                "log_destination": "kafka",
                "log_name": "app",
            },
        )
        assert "log_destination" in errors

    def test_missing_log_name_fails(self):
        errors = _errors(
            LoggingInputSerializer,
            {
                "log_destination": "cloudwatch",
            },
        )
        assert "log_name" in errors


# ---------------------------------------------------------------------------
# EmailInputSerializer
# ---------------------------------------------------------------------------


class TestEmailInputSerializer:
    def test_console_type_passes(self):
        data = _valid(
            EmailInputSerializer,
            {
                "email_type": "console",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
            },
        )
        assert data["email_type"] == "console"

    def test_smtp_with_all_fields_passes(self):
        data = _valid(
            EmailInputSerializer,
            {
                "email_type": "smtp",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "smtp_enc_type": "starttls",
            },
        )
        assert data["smtp_host"] == "smtp.example.com"

    def test_smtp_with_auth_passes(self):
        data = _valid(
            EmailInputSerializer,
            {
                "email_type": "smtp",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "smtp_enc_type": "starttls",
                "smtp_auth_enabled": True,
                "smtp_username": "user",
                "smtp_password": "pass",
            },
        )
        assert data["smtp_auth_enabled"] is True

    def test_smtp_missing_host_fails(self):
        errors = _errors(
            EmailInputSerializer,
            {
                "email_type": "smtp",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
                "smtp_port": 587,
                "smtp_enc_type": "starttls",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_smtp_missing_port_fails(self):
        errors = _errors(
            EmailInputSerializer,
            {
                "email_type": "smtp",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
                "smtp_host": "smtp.example.com",
                "smtp_enc_type": "starttls",
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_smtp_auth_enabled_missing_credentials_fails(self):
        errors = _errors(
            EmailInputSerializer,
            {
                "email_type": "smtp",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "smtp_enc_type": "starttls",
                "smtp_auth_enabled": True,
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_invalid_from_address_fails(self):
        errors = _errors(
            EmailInputSerializer,
            {
                "email_type": "console",
                "from_address": "not-an-email",
                "from_name": "Planner",
            },
        )
        assert "from_address" in errors

    def test_smtp_port_zero_fails(self):
        errors = _errors(
            EmailInputSerializer,
            {
                "email_type": "smtp",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
                "smtp_host": "smtp.example.com",
                "smtp_port": 0,
                "smtp_enc_type": "none",
            },
        )
        assert "smtp_port" in errors

    def test_smtp_port_above_max_fails(self):
        errors = _errors(
            EmailInputSerializer,
            {
                "email_type": "smtp",
                "from_address": "noreply@example.com",
                "from_name": "Planner",
                "smtp_host": "smtp.example.com",
                "smtp_port": 70000,
                "smtp_enc_type": "none",
            },
        )
        assert "smtp_port" in errors


# ---------------------------------------------------------------------------
# SetupInputSerializer (top-level composite)
# ---------------------------------------------------------------------------


class TestSetupInputSerializer:
    def test_valid_full_payload_passes(self):
        data = _valid(SetupInputSerializer, _valid_setup_payload())
        assert "admin" in data
        assert "app" in data

    def test_missing_admin_section_fails(self):
        payload = _valid_setup_payload()
        del payload["admin"]
        errors = _errors(SetupInputSerializer, payload)
        assert "admin" in errors

    def test_missing_infra_section_fails(self):
        payload = _valid_setup_payload()
        del payload["infra"]
        errors = _errors(SetupInputSerializer, payload)
        assert "infra" in errors

    def test_missing_db_section_fails(self):
        payload = _valid_setup_payload()
        del payload["db"]
        errors = _errors(SetupInputSerializer, payload)
        assert "db" in errors

    def test_missing_auth_section_fails(self):
        payload = _valid_setup_payload()
        del payload["auth"]
        errors = _errors(SetupInputSerializer, payload)
        assert "auth" in errors

    def test_missing_storage_section_fails(self):
        payload = _valid_setup_payload()
        del payload["storage"]
        errors = _errors(SetupInputSerializer, payload)
        assert "storage" in errors

    def test_missing_email_section_fails(self):
        payload = _valid_setup_payload()
        del payload["email"]
        errors = _errors(SetupInputSerializer, payload)
        assert "email" in errors

    def test_missing_logging_section_fails(self):
        payload = _valid_setup_payload()
        del payload["logging"]
        errors = _errors(SetupInputSerializer, payload)
        assert "logging" in errors


# ---------------------------------------------------------------------------
# DbTestInputSerializer
# ---------------------------------------------------------------------------


class TestDbTestInputSerializer:
    def test_valid_payload_passes(self):
        data = _valid(
            DbTestInputSerializer,
            {
                "host": "localhost",
                "port": "5432",
                "db_name": "mydb",
                "user_name": "admin",
                "password": "secret",
            },
        )
        assert data["host"] == "localhost"

    def test_missing_host_fails(self):
        errors = _errors(
            DbTestInputSerializer,
            {
                "port": "5432",
                "db_name": "mydb",
                "user_name": "admin",
                "password": "secret",
            },
        )
        assert "host" in errors

    def test_missing_password_fails(self):
        errors = _errors(
            DbTestInputSerializer,
            {
                "host": "localhost",
                "port": "5432",
                "db_name": "mydb",
                "user_name": "admin",
            },
        )
        assert "password" in errors


# ---------------------------------------------------------------------------
# EmailTestInputSerializer
# ---------------------------------------------------------------------------


class TestEmailTestInputSerializer:
    def test_console_with_from_address_passes(self):
        data = _valid(
            EmailTestInputSerializer,
            {
                "email_type": "console",
                "from_address": "test@example.com",
            },
        )
        assert data["email_type"] == "console"

    def test_smtp_with_all_fields_passes(self):
        data = _valid(
            EmailTestInputSerializer,
            {
                "email_type": "smtp",
                "from_address": "test@example.com",
                "smtp_host": "smtp.example.com",
                "smtp_port": 465,
                "smtp_enc_type": "ssl",
            },
        )
        assert data["smtp_host"] == "smtp.example.com"

    def test_smtp_with_auth_missing_credentials_fails(self):
        errors = _errors(
            EmailTestInputSerializer,
            {
                "email_type": "smtp",
                "from_address": "test@example.com",
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "smtp_enc_type": "starttls",
                "smtp_auth_enabled": True,
            },
        )
        assert "non_field_errors" in errors or "missing_fields" in str(errors)

    def test_invalid_from_address_fails(self):
        errors = _errors(
            EmailTestInputSerializer,
            {
                "email_type": "console",
                "from_address": "bad-email",
            },
        )
        assert "from_address" in errors
