import os

from pycore.crypto import fernet_decrypt

from apps.configurations.converters import get_bool
from apps.configurations.defaults import CONFIGURATION_DEFAULTS
from apps.configurations.models import Configuration


def get_config_id(config_code: str):
    obj = Configuration.objects.get(config_code=config_code)
    return obj.code


def get_config_value(config_code: str, fallback_default=True):
    try:
        obj = Configuration.objects.get(config_code=config_code)
        value = obj.value
        is_secret = obj.is_secret
    except Configuration.DoesNotExist:
        if not fallback_default:
            raise

        default = CONFIGURATION_DEFAULTS.get(config_code)
        if default is None:
            raise

        value = default.get("value")
        is_secret = default.get("is_secret", False)

    if is_secret:
        if value.startswith("enc:"):
            fernet_key = os.environ.get("FERNET_KEY", "")
            if fernet_key:
                value = fernet_decrypt(value, fernet_key)
        elif value.startswith("aws:"):
            from awscore import SecretsManager

            secret_name = value.removeprefix("aws:")
            region = os.environ.get("AWS_REGION", "")
            access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
            secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
            sm = SecretsManager(
                region=region, access_key=access_key, secret_key=secret_key
            )
            value = sm.get(secret_name)

    return value


class General:
    @staticmethod
    def get_app_name():
        return get_config_value("APP_NAME")

    @staticmethod
    def get_app_url():
        return get_config_value("APP_URL")


class Setup:
    @staticmethod
    def get_setup_complete():
        return get_bool(get_config_value("SETUP_COMPLETE"), False)

    @staticmethod
    def is_setup_complete():
        return Setup.get_setup_complete()


class Auth:
    @staticmethod
    def get_auth_mode():
        from apps.auth.constants import AuthMode

        mode = get_config_value("AUTH_MODE")
        return AuthMode(mode)

    @staticmethod
    def get_allow_registration():
        return get_bool(get_config_value("ALLOW_REGISTRATION"), False)

    @staticmethod
    def is_self_registration_allowed():
        from apps.auth.constants import AuthMode

        return (
            Auth.get_auth_mode() == AuthMode.CLASSIC and Auth.get_allow_registration()
        )


class Infra:
    @staticmethod
    def get_deployment_type():
        from apps.setup.constants import DeploymentType

        type_ = get_config_value("DEPLOYMENT_TYPE")
        return DeploymentType(type_)

    @staticmethod
    def get_secrets_prefix():
        return get_config_value("SECRETS_PREFIX").rstrip("/")

    @staticmethod
    def get_storage_type():
        from apps.setup.constants import StorageType

        type_ = get_config_value("STORAGE_TYPE")
        return StorageType(type_)

    @staticmethod
    def get_storage_path():
        return get_config_value("STORAGE_PATH")


class Email:
    @staticmethod
    def get_email_type():
        from apps.setup.constants import EmailType

        type_ = get_config_value("EMAIL_TYPE")
        return EmailType(type_)

    @staticmethod
    def get_email_from_address():
        return get_config_value("EMAIL_FROM_ADDRESS")

    @staticmethod
    def get_email_from_name():
        return get_config_value("EMAIL_FROM_NAME")

    @staticmethod
    def get_smtp_host() -> str:
        return get_config_value("EMAIL_SMTP_HOST")

    @staticmethod
    def get_smtp_port() -> int:
        return int(get_config_value("EMAIL_SMTP_PORT"))

    @staticmethod
    def get_smtp_enc_type() -> str:
        return get_config_value("EMAIL_SMTP_ENC_TYPE")

    @staticmethod
    def is_smtp_auth_enabled() -> bool:
        return get_bool(get_config_value("EMAIL_SMTP_AUTH_ENABLED"), False)

    @staticmethod
    def get_smtp_username() -> str:
        return get_config_value("EMAIL_SMTP_USERNAME")

    @staticmethod
    def get_smtp_password() -> str:
        return get_config_value("EMAIL_SMTP_PASSWORD")


class Holidays:
    @staticmethod
    def get_default_holidays() -> int:
        return int(get_config_value("DEFAULT_HOLIDAYS"))


class FinancialYear:
    @staticmethod
    def get_fy_expiry_warning_days() -> int:
        return int(get_config_value("FY_EXPIRY_WARNING_DAYS"))


class Users:
    @staticmethod
    def get_password_reset_timeout() -> int:
        return int(get_config_value("PASSWORD_RESET_TIMEOUT"))


class Sprint:
    @staticmethod
    def get_sprint_name_prefix() -> str:
        return get_config_value("SPRINT_NAME_PREFIX")

    @staticmethod
    def get_sprint_start_number() -> int:
        return int(get_config_value("SPRINT_START_NUMBER"))

    @staticmethod
    def get_sprint_duration_days() -> int:
        return int(get_config_value("SPRINT_DURATION_DAYS"))

    @staticmethod
    def get_sprint_point_price() -> int:
        return int(get_config_value("SPRINT_POINT_PRICE"))


class Project:
    @staticmethod
    def get_size_xs_max_amount() -> int:
        return int(get_config_value("PROJECT_SIZE_XS_MAX_AMOUNT"))

    @staticmethod
    def get_size_s_max_amount() -> int:
        return int(get_config_value("PROJECT_SIZE_S_MAX_AMOUNT"))

    @staticmethod
    def get_size_m_max_amount() -> int:
        return int(get_config_value("PROJECT_SIZE_M_MAX_AMOUNT"))

    @staticmethod
    def get_size_l_max_amount() -> int:
        return int(get_config_value("PROJECT_SIZE_L_MAX_AMOUNT"))


class AI:
    @staticmethod
    def is_ai_enabled() -> bool:
        return get_bool(get_config_value("AI_ENABLED"), False)

    @staticmethod
    def get_ai_provider() -> str:
        return get_config_value("AI_PROVIDER")

    @staticmethod
    def get_ai_model() -> str:
        return get_config_value("AI_MODEL")

    @staticmethod
    def get_anthropic_api_key() -> str:
        return get_config_value("AI_ANTHROPIC_API_KEY")

    @staticmethod
    def get_bedrock_region() -> str:
        return get_config_value("AI_BEDROCK_REGION")

    @staticmethod
    def get_bedrock_auth_mode() -> str:
        return get_config_value("AI_BEDROCK_AUTH_MODE")

    @staticmethod
    def get_bedrock_iam_key() -> str:
        return get_config_value("AI_BEDROCK_IAM_KEY")

    @staticmethod
    def get_bedrock_iam_secret() -> str:
        return get_config_value("AI_BEDROCK_IAM_SECRET")
