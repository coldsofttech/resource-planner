import logging
import os

from django.db import transaction

from apps.core.exceptions import ConflictException
from apps.core.services import ContextService
from apps.setup.constants import DatabaseType, DeploymentType, EmailType, StorageType

logger = logging.getLogger(__name__)


class SetupService(ContextService):
    def _user_service(self):
        from apps.users.services import AdminUserService

        return AdminUserService(user=self.user, request=self.request)

    def _config_service(self):
        from apps.configurations.services import AdminConfigurationService

        return AdminConfigurationService(user=self.user, request=self.request)

    def _oauth_service(self):
        from apps.oauth.services import AdminOAuthService

        return AdminOAuthService(user=self.user, request=self.request)

    def _saml_service(self):
        from apps.saml.services import AdminSAMLService

        return AdminSAMLService(user=self.user, request=self.request)

    def _test_service(self):
        return TestService(user=self.user, request=self.request)

    def _db_engine_service(self):
        from apps.setup.engine import DatabaseEngineService

        return DatabaseEngineService(user=self.user, request=self.request)

    def _create_admin_user(self, *, first_name, last_name, email, password):
        self._user_service().create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        logger.info("Admin user '%s' created successfully.", email)

    def _set_app_details(self, *, app_name, app_url):
        self._config_service().set_config(config_code="APP_NAME", value=app_name)
        logger.info("Application name set to: '%s'.", app_name)
        self._config_service().set_config(config_code="APP_URL", value=app_url)
        logger.info("Application URL set to: '%s'.", app_url)

    def _write_infra_env(
        self,
        *,
        deployment_type,
        fernet_key=None,
        aws_region=None,
        secrets_prefix=None,
        aws_auth_mode=None,
        aws_access_key_id=None,
        aws_secret_access_key=None,
    ):
        """Write infrastructure config to .env and os.environ only — no DB writes.

        DB_PASSWORD_SOURCE and SECRETS_PREFIX must be in the environment before
        _create_db_configs() runs so that method can resolve the password correctly.
        """
        from django.conf import settings
        from pycore import DotEnv

        env = DotEnv(settings.BASE_DIR)

        if deployment_type == DeploymentType.LOCAL:
            env.write("FERNET_KEY", fernet_key)
            env.write("SECRETS_PREFIX", "")
            env.write("DB_PASSWORD_SOURCE", "env")
            env.write("DB_SECRET_NAME", "")
            os.environ["FERNET_KEY"] = fernet_key
            os.environ["SECRETS_PREFIX"] = ""
            os.environ["DB_PASSWORD_SOURCE"] = "env"  # nosec B105
            os.environ.pop("DB_SECRET_NAME", None)
        elif deployment_type == DeploymentType.AWS:
            prefix = secrets_prefix.rstrip("/")
            db_secret_name = f"{prefix}/db"

            env.write("SECRETS_PREFIX", prefix)
            env.write("AWS_REGION", aws_region)
            env.write("AWS_DEFAULT_REGION", aws_region)
            env.write("DB_PASSWORD_SOURCE", "aws")
            env.write("DB_SECRET_NAME", db_secret_name)
            os.environ["SECRETS_PREFIX"] = prefix
            os.environ["AWS_REGION"] = aws_region
            os.environ["AWS_DEFAULT_REGION"] = aws_region
            os.environ["DB_PASSWORD_SOURCE"] = "aws"  # nosec B105
            os.environ["DB_SECRET_NAME"] = db_secret_name

            if aws_auth_mode == "user":
                env.write("AWS_ACCESS_KEY_ID", aws_access_key_id)
                env.write("AWS_SECRET_ACCESS_KEY", aws_secret_access_key)
                os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key_id
                os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_access_key

        logger.info(
            "Infrastructure configuration written to .env (deployment=%s).",
            deployment_type,
        )

    def _save_infra_db_configs(self, *, deployment_type):
        """Persist infra config values to the database.

        Called after _write_infra_env() and any database switch, so that the
        records land in the correct (final) database.  SECRETS_PREFIX is read
        from os.environ because _write_infra_env() already normalised it.
        """
        self._config_service().set_config(
            config_code="DEPLOYMENT_TYPE", value=deployment_type.value
        )
        logger.info(
            "Infrastructure DB configs saved (deployment=%s).", deployment_type.value
        )
        self._config_service().set_config(
            config_code="SECRETS_PREFIX", value=os.environ.get("SECRETS_PREFIX", "")
        )

    def _save_infra_storage_configs(self, *, storage):
        """Persist infra storage config values to the database"""
        storage_type = StorageType(storage["storage_type"])
        self._config_service().set_config(
            config_code="STORAGE_TYPE", value=storage_type.value
        )
        logger.info(
            "Infrastructure storage configs saved (deployment=%s).", storage_type.value
        )

        if (
            storage_type == StorageType.FILE_SYSTEM
            or storage_type == StorageType.AMAZON_S3
        ):
            self._config_service().set_config(
                config_code="STORAGE_PATH", value=storage["storage_path"]
            )

    def _save_email_configs(self, *, email_data):
        """Persist email config values to the database"""
        email_type = EmailType(email_data["email_type"])

        self._config_service().set_config(
            config_code="EMAIL_TYPE", value=email_type.value
        )
        self._config_service().set_config(
            config_code="EMAIL_FROM_ADDRESS", value=email_data["from_address"]
        )
        self._config_service().set_config(
            config_code="EMAIL_FROM_NAME", value=email_data["from_name"]
        )

        if email_type == EmailType.SMTP:
            self._config_service().set_config(
                config_code="EMAIL_SMTP_HOST", value=email_data.get("smtp_host", "")
            )
            self._config_service().set_config(
                config_code="EMAIL_SMTP_PORT", value=email_data.get("smtp_port", 587)
            )
            self._config_service().set_config(
                config_code="EMAIL_SMTP_ENC_TYPE",
                value=email_data.get("smtp_enc_type", "none"),
            )
            self._config_service().set_config(
                config_code="EMAIL_SMTP_AUTH_ENABLED",
                value=email_data.get("smtp_auth_enabled", False),
            )
            if email_data.get("smtp_auth_enabled"):
                self._config_service().set_config(
                    config_code="EMAIL_SMTP_USERNAME",
                    value=email_data.get("smtp_username", ""),
                )
                self._config_service().set_config(
                    config_code="EMAIL_SMTP_PASSWORD",
                    value=email_data.get("smtp_password", ""),
                )

        logger.info("Email configs saved (type=%s).", email_type.value)

    def _create_db_configs(
        self, *, deployment_type, engine, host, port, db_name, user_name, password
    ):
        from django.conf import settings
        from pycore import DotEnv

        is_aws = deployment_type == DeploymentType.AWS

        if engine == DatabaseType.POSTGRESQL:
            self._test_service().test_db_connection(
                host=host,
                port=port,
                db_name=db_name,
                user_name=user_name,
                password=password,
            )

        env = DotEnv(settings.BASE_DIR)
        env.write("DB_ENGINE", engine.value)
        os.environ["DB_ENGINE"] = engine.value

        if engine == DatabaseType.POSTGRESQL:
            connection_fields = {
                "DB_HOST": host or "",
                "DB_PORT": port or "",
                "DB_NAME": db_name or "",
                "DB_USER": user_name or "",
            }
            for key, value in connection_fields.items():
                env.write(key, value)
                os.environ[key] = value

            if is_aws:
                from awscore import SecretsManager

                region = os.environ.get("AWS_REGION", "")
                access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
                secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
                db_secret_name = os.environ.get("DB_SECRET_NAME", "")
                sm = SecretsManager(
                    region=region, access_key=access_key, secret_key=secret_key
                )
                sm.put_or_update(
                    db_secret_name,
                    password,
                    description="Database password for Resource Planner",
                )
                logger.info(
                    "DB password stored in Secrets Manager as '%s'.", db_secret_name
                )
            else:
                env.write("DB_PASSWORD", password)
                os.environ["DB_PASSWORD"] = password

            self._db_engine_service().to_postgresql()

        logger.info("Database configuration written to .env (engine=%s).", engine.value)

    def _set_auth_type(self, *, auth_data):
        from apps.auth.constants import AuthMode

        auth_type = AuthMode(auth_data["auth_type"])
        self._config_service().set_config(
            config_code="AUTH_MODE", value=auth_type.value
        )

        if auth_type == AuthMode.CLASSIC:
            self._config_service().set_config(
                config_code="ALLOW_REGISTRATION", value=auth_data.get("self_register")
            )
        elif auth_type == AuthMode.SAML:
            self._saml_service().create(
                name=auth_data.get("provider_name"),
                idp_entity_id=auth_data.get("idp_entity_id"),
                idp_sso_url=auth_data.get("idp_sso_url"),
                idp_x509_cert=auth_data.get("idp_x509_cert"),
                sp_entity_id=auth_data.get("sp_entity_id"),
                sp_assertion_url=auth_data.get("sp_assertion_url"),
            )
        elif auth_type == AuthMode.OAUTH:
            self._oauth_service().create(
                name=auth_data.get("provider_name"),
                client_id=auth_data.get("client_id"),
                client_secret=auth_data.get("client_secret"),
                auth_endpoint=auth_data.get("auth_endpoint"),
                token_endpoint=auth_data.get("token_endpoint"),
                userinfo_endpoint=auth_data.get("userinfo_endpoint"),
                scope=auth_data.get("scope"),
            )

        logger.info("Authentication type set to: '%s'.", auth_type)

    def _create_logging_configs(
        self,
        *,
        log_destination,
        log_name,
        log_path=None,
        log_rotation="none",
        log_rotation_size_mb=None,
        log_cleanup_keep_files=None,
        log_cleanup_keep_days=None,
        log_s3_bucket=None,
    ):
        from django.conf import settings
        from pycore import DotEnv

        env = DotEnv(settings.BASE_DIR)

        env_fields = {
            "LOG_DESTINATION": log_destination,
            "LOG_NAME": log_name,
            "LOG_PATH": log_path or "",
            "LOG_ROTATION": log_rotation,
            "LOG_ROTATION_SIZE_MB": str(log_rotation_size_mb or 10),
            "LOG_CLEANUP_KEEP_FILES": str(log_cleanup_keep_files or 5),
            "LOG_CLEANUP_KEEP_DAYS": str(log_cleanup_keep_days or 0),
            "LOG_S3_BUCKET": log_s3_bucket or "",
        }
        for key, value in env_fields.items():
            env.write(key, value)
            os.environ[key] = value

        logger.info(
            "Logging configuration written to .env (destination=%s).", log_destination
        )

    def _mark_setup_complete(self):
        self._config_service().set_config(config_code="SETUP_COMPLETE", value=True)
        logger.info("Initial setup is now complete.")

    def create(self, *, admin, app, infra, db, auth, storage, email, logging):
        from apps.configurations.selectors import Setup
        from apps.setup import status as _status

        if Setup.get_setup_complete():
            raise ConflictException("Setup has already been completed.")

        _status.start()

        try:
            # Phase 1: write all env vars and potentially switch the live database.
            # No ORM writes happen here so there is no transaction to worry about.
            self._write_infra_env(
                deployment_type=DeploymentType(infra["deployment_type"]),
                fernet_key=infra.get("fernet_key"),
                aws_region=infra.get("aws_region"),
                secrets_prefix=infra.get("secrets_prefix"),
                aws_auth_mode=infra.get("aws_auth_mode"),
                aws_access_key_id=infra.get("aws_access_key_id"),
                aws_secret_access_key=infra.get("aws_secret_access_key"),
            )
            _status.advance("infra")

            self._create_db_configs(
                deployment_type=DeploymentType(infra["deployment_type"]),
                engine=DatabaseType(db["engine"]),
                host=db.get("host") or "",
                port=db.get("port") or "",
                db_name=db.get("db_name") or "",
                user_name=db.get("user_name") or "",
                password=db.get("password") or "",
            )
            _status.advance("database")

            self._create_logging_configs(
                log_destination=logging["log_destination"],
                log_name=logging["log_name"],
                log_path=logging.get("log_path"),
                log_rotation=logging.get("log_rotation", "none"),
                log_rotation_size_mb=logging.get("log_rotation_size_mb"),
                log_cleanup_keep_files=logging.get("log_cleanup_keep_files"),
                log_cleanup_keep_days=logging.get("log_cleanup_keep_days"),
                log_s3_bucket=logging.get("log_s3_bucket"),
            )
            _status.advance("logging")

            # Phase 2: all ORM writes go to the now-correct database.
            with transaction.atomic():
                self._create_admin_user(
                    first_name=admin["first_name"],
                    last_name=admin["last_name"],
                    email=admin["email"],
                    password=admin["password"],
                )
                _status.advance("admin")

                self._set_app_details(
                    app_name=app["app_name"],
                    app_url=app["app_url"],
                )
                self._save_infra_db_configs(
                    deployment_type=DeploymentType(infra["deployment_type"]),
                )
                _status.advance("app")

                self._set_auth_type(auth_data=auth)
                _status.advance("auth")

                self._save_infra_storage_configs(storage=storage)
                _status.advance("storage")

                self._save_email_configs(email_data=email)
                _status.advance("email")

                self._mark_setup_complete()
                _status.advance("complete")

            _status.complete()

        except Exception as exc:
            _status.fail(str(exc))
            raise


class TestService(ContextService):
    def test_email_connection(
        self,
        *,
        email_type,
        from_address,
        from_name="",
        smtp_host="",
        smtp_port=587,
        smtp_enc_type="none",
        smtp_auth_enabled=False,
        smtp_username="",
        smtp_password="",
    ):
        from emailcore import EmailSender

        from apps.core.exceptions import ValidationException

        try:
            sender = EmailSender(
                email_type=email_type,
                from_address=from_address,
                from_name=from_name,
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                smtp_enc_type=smtp_enc_type,
                smtp_auth_enabled=smtp_auth_enabled,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
            )
            sender.send(
                to=from_address,
                subject="Resource Planner — Email Test",
                body=(
                    "This is a test email from the Resource Planner setup wizard.\n\n"
                    "If you receive this, your email configuration is "
                    "working correctly."
                ),
            )
        except Exception as exc:
            raise ValidationException(str(exc)) from exc

        logger.info("Email connection test succeeded (type=%s).", email_type)

    def test_db_connection(self, *, host, port, db_name, user_name, password):
        from apps.core.exceptions import ValidationException

        try:
            import psycopg2
        except ImportError as exc:
            raise ValidationException("psycopg2 is not installed.") from exc

        try:
            conn = psycopg2.connect(
                host=host,
                port=int(port),
                dbname=db_name,
                user=user_name,
                password=password,
                connect_timeout=5,
            )
            conn.close()
        except Exception as exc:
            raise ValidationException(str(exc)) from exc

        logger.info(
            "PostgreSQL connection test succeeded (host=%s, port=%s, db=%s).",
            host,
            port,
            db_name,
        )
