import os

from pycore import fernet_encrypt


def encrypt_value(value: str, secret_name: str) -> str:
    """Encrypt a secret according to the active deployment type.

    local  → Fernet-encrypts using FERNET_KEY env var, returns "enc:<ciphertext>"
    aws    → stores in AWS Secrets Manager under secret_name, returns
             "aws:<secret_name>"

    Falls back to the plain string value for unknown deployment types.
    """
    from apps.configurations.selectors import Infra
    from apps.setup.constants import DeploymentType

    deployment_type = Infra.get_deployment_type()

    if deployment_type == DeploymentType.LOCAL:
        fernet_key = os.environ.get("FERNET_KEY", "")
        return fernet_encrypt(str(value), fernet_key)

    if deployment_type == DeploymentType.AWS:
        from awscore import SecretsManager

        region = os.environ.get("AWS_REGION", "")
        access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
        aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        sm = SecretsManager(
            region=region, access_key=access_key, secret_key=aws_secret_key
        )
        sm.put_or_update(secret_name, str(value))
        return f"aws:{secret_name}"

    return str(value)
