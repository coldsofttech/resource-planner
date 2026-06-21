import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _enable_sqlite_wal(sender, connection, **kwargs):
    """Switch SQLite to WAL journal mode on every new connection.

    WAL allows concurrent reads and a writer to coexist, eliminating the
    "database is locked" errors that occur in the dev server's threaded mode.
    Only applied to SQLite; PostgreSQL is unaffected.

    Registered in CoreConfig.on_ready() with dispatch_uid="enable_sqlite_wal"
    so that Django's StatReloader does not accumulate duplicate handlers across
    module reloads.
    """
    if connection.vendor == "sqlite":
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")


def _resolve_db_password() -> str:
    source = os.environ.get("DB_PASSWORD_SOURCE", "env").lower()

    if source == "aws":
        import json

        import boto3
        from botocore.exceptions import ClientError

        secret_name = os.environ.get("DB_SECRET_NAME", "resource-planner/db/password")
        region = os.environ.get(
            "AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "eu-west-1")
        )
        secret_key = os.environ.get("DB_SECRET_KEY", "password")
        endpoint_url = os.environ.get("AWS_ENDPOINT", "")

        try:
            client_kwargs: dict = {"region_name": region}
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url
            client = boto3.client("secretsmanager", **client_kwargs)
            response = client.get_secret_value(SecretId=secret_name)
            raw = response.get("SecretString", "")

            try:
                return json.loads(raw).get(secret_key, raw)
            except (json.JSONDecodeError, AttributeError):
                return raw
        except ClientError as exc:
            import logging

            code = exc.response.get("Error", {}).get("Code", "UnknownError")
            logging.getLogger(__name__).error(
                "Failed to fetch DB password from AWS Secrets Manager: %s",
                code,
            )
            return ""

    return os.environ.get("DB_PASSWORD", "")


def build_databases() -> dict:
    """Build the DATABASES dict from the current environment.

    Called at startup (to produce the frozen DATABASES value in settings.py)
    and again at runtime when the setup wizard switches from SQLite to PostgreSQL.
    """
    engine = os.environ.get("DB_ENGINE", "sqlite").lower()

    if engine == "postgresql":
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.environ.get("DB_NAME", "resourceplanner"),
                "USER": os.environ.get("DB_USER", "postgres"),
                "PASSWORD": _resolve_db_password(),
                "HOST": os.environ.get("DB_HOST", "localhost"),
                "PORT": os.environ.get("DB_PORT", "5432"),
                "OPTIONS": {"connect_timeout": 10},
                "TEST": {
                    "NAME": "test_resourceplanner",
                },
            }
        }

    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
            "OPTIONS": {"timeout": 20},
            "TEST": {
                "NAME": ":memory:",
            },
        }
    }


# Engine Selection:
#   DB_ENGINE=sqlite        > SQLite (default, local dev / pre-setup bootstrap)
#   DB_ENGINE=postgresql    > PostgreSQL
#
# PostgreSQL connection env vars:
#   DB_NAME, DB_USER, DB_HOST, DB_PORT
#
# Password resolution (DB_PASSWORD_SOURCE):
#   env (default)           > DB_PASSWORD env var
#   aws                     > AWS Secrets Manager, secret named DB_SECRET_NAME
#                             expects either a plain string or JSON {"password": "..."}
#                             key overridable via DB_SECRET_KEY (default "password")
DATABASES = build_databases()
