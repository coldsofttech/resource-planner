import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecretsManager:
    """Thin wrapper around AWS Secrets Manager for Resource Planner secrets."""

    def __init__(
        self,
        region: str,
        access_key: str = "",
        secret_key: str = "",
        endpoint_url: str = "",
    ):  # nosec B107
        kwargs: dict = {"region_name": region}
        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self._client = boto3.client("secretsmanager", **kwargs)

    def list(self, prefix: str) -> list[str]:
        """Return secret names that start with *prefix*."""
        names: list[str] = []
        paginator = self._client.get_paginator("list_secrets")
        for page in paginator.paginate(Filters=[{"Key": "name", "Values": [prefix]}]):
            names.extend(s["Name"] for s in page.get("SecretList", []))
        return names

    def get(self, name: str) -> str:
        """Retrieve the string value of a secret. Raises if not found."""
        try:
            response = self._client.get_secret_value(SecretId=name)
            return response.get("SecretString", "")
        except ClientError as exc:
            logger.error("Failed to retrieve secret '%s': %s", name, exc)
            raise

    def put(self, name: str, value: str, description: str = "") -> None:
        """Create a new secret. Raises if it already exists."""
        kwargs: dict = {"Name": name, "SecretString": value}
        if description:
            kwargs["Description"] = description
        try:
            self._client.create_secret(**kwargs)
            logger.info("Secret '%s' created.", name)
        except ClientError as exc:
            logger.error("Failed to create secret '%s': %s", name, exc)
            raise

    def update(self, name: str, value: str) -> None:
        """Update the value of an existing secret."""
        try:
            self._client.put_secret_value(SecretId=name, SecretString=value)
            logger.info("Secret '%s' updated.", name)
        except ClientError as exc:
            logger.error("Failed to update secret '%s': %s", name, exc)
            raise

    def put_or_update(self, name: str, value: str, description: str = "") -> None:
        """Create the secret if it does not exist, otherwise update its value."""
        try:
            self.update(name, value)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ResourceNotFoundException":
                self.put(name, value, description=description)
            else:
                raise

    def delete(self, name: str, force: bool = False) -> None:
        """Delete a secret. Set *force* to skip the recovery window."""
        try:
            self._client.delete_secret(
                SecretId=name,
                ForceDeleteWithoutRecovery=force,
            )
            logger.info("Secret '%s' deleted (force=%s).", name, force)
        except ClientError as exc:
            logger.error("Failed to delete secret '%s': %s", name, exc)
            raise
