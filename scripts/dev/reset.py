import argparse
import os
import sys
from pathlib import Path

_tty = sys.stdout.isatty()
YELLOW = "\033[93m" if _tty else ""
RED = "\033[91m" if _tty else ""
RESET = "\033[0m" if _tty else ""

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "apps" / "web"


def _bootstrap_django():
    sys.path.insert(0, str(WEB_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # Force console-only logging so django.setup() never touches the log file.
    # DotEnv.load_environ() uses setdefault, so this value won't be overwritten by .env.
    os.environ["LOG_DESTINATION"] = ""

    import django

    django.setup()


def main(full_clean: bool = False):
    _bootstrap_django()

    from apps.configurations.models import Configuration
    from apps.users.models import User, UserProfile
    from django.conf import settings
    from pycore import DotEnv

    scope = (
        "admin user, user profile, setup configuration, OAuth, and SAML records"
        if full_clean
        else "admin user, user profile, and setup configuration"
    )
    print(f"\n{YELLOW}!!! WARNING: This is a destructive operation !!!{RESET}")
    print(f"{YELLOW}Deletes the {scope}.{RESET}")
    confirm = input("\nType 'yes' to continue: ").strip().lower()

    if confirm != "yes":
        print(f"{RED}Aborted.{RESET}")
        return

    config_codes = [
        "SETUP_COMPLETE",
        "APP_NAME",
        "APP_URL",
        "AUTH_MODE",
        "ALLOW_REGISTRATION",
        "DEPLOYMENT_TYPE",
        "SECRETS_PREFIX",
        "STORAGE_TYPE",
        "STORAGE_PATH",
        "EMAIL_TYPE",
        "EMAIL_FROM_ADDRESS",
        "EMAIL_FROM_NAME",
        "EMAIL_SMTP_HOST",
        "EMAIL_SMTP_PORT",
        "EMAIL_SMTP_ENC_TYPE",
        "EMAIL_SMTP_AUTH_ENABLED",
        "EMAIL_SMTP_USERNAME",
        "EMAIL_SMTP_PASSWORD",
    ]
    deleted, _ = Configuration.objects.filter(config_code__in=config_codes).delete()
    print(f"Configuration records deleted: {deleted}")

    superuser_ids = list(
        User.objects.filter(is_superuser=True).values_list("id", flat=True)
    )
    if superuser_ids:
        profile_deleted, _ = UserProfile.objects.filter(
            user_id__in=superuser_ids
        ).delete()
        print(f"UserProfile records deleted: {profile_deleted}")

    user_deleted, _ = User.objects.filter(is_superuser=True).delete()
    print(f"User records deleted: {user_deleted}")

    if full_clean:
        from apps.oauth.models import OAuth
        from apps.saml.models import SAML

        oauth_deleted, _ = OAuth.objects.all().delete()
        print(f"OAuth records deleted: {oauth_deleted}")

        saml_deleted, _ = SAML.objects.all().delete()
        print(f"SAML records deleted: {saml_deleted}")

    env = DotEnv(settings.BASE_DIR)

    env_keys = [
        # Database
        "DB_ENGINE",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_PASSWORD_SOURCE",
        "DB_SECRET_NAME",
        # Infrastructure / secrets
        "FERNET_KEY",
        "SECRETS_PREFIX",
        # AWS
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        # Logging
        "LOG_DESTINATION",
        "LOG_NAME",
        "LOG_PATH",
        "LOG_ROTATION",
        "LOG_ROTATION_SIZE_MB",
        "LOG_CLEANUP_KEEP_FILES",
        "LOG_CLEANUP_KEEP_DAYS",
        "LOG_S3_BUCKET",
    ]
    cleared = [key for key in env_keys if env.delete(key)]
    if cleared:
        print(f"Environment keys cleared: {', '.join(cleared)}")

    print("\nReset complete. Setup wizard will appear on next visit.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset setup state for development.")
    parser.add_argument(
        "--full-clean",
        action="store_true",
        help="Also wipe all OAuth and SAML records.",
    )
    args = parser.parse_args()
    main(full_clean=args.full_clean)
