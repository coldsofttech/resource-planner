from __future__ import annotations

import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Client:
    """Thin boto3 wrapper for S3 put / get / delete operations."""

    def __init__(
        self,
        region: str,
        access_key: str = "",
        secret_key: str = "",
        endpoint_url: str = "",
    ):
        if not endpoint_url:
            endpoint_url = os.environ.get("AWS_ENDPOINT", "")
        kwargs: dict = {"region_name": region}
        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self._client = boto3.client("s3", **kwargs)

    def put(
        self,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        try:
            self._client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
        except ClientError as exc:
            logger.error("S3 put failed for s3://%s/%s: %s", bucket, key, exc)
            raise

    def get(self, bucket: str, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as exc:
            logger.error("S3 get failed for s3://%s/%s: %s", bucket, key, exc)
            raise

    def delete(self, bucket: str, key: str) -> None:
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            logger.error("S3 delete failed for s3://%s/%s: %s", bucket, key, exc)
            raise
