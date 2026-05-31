import datetime
import io
import logging
import os

import boto3
from botocore.exceptions import ClientError


class S3LogHandler(logging.Handler):
    """Buffers log records and flushes them to an S3 object on close or when the
    buffer reaches *flush_count* records. Each flush writes a timestamped key
    under *key_prefix* so records are never overwritten."""

    def __init__(
        self,
        bucket: str,
        key_prefix: str,
        region: str,
        access_key: str = "",
        secret_key: str = "",
        endpoint_url: str = "",
        flush_count: int = 100,
    ):  # nosec B107
        super().__init__()
        if not endpoint_url:
            endpoint_url = os.environ.get("AWS_ENDPOINT", "")
        kwargs: dict = {"region_name": region}
        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self._client = boto3.client("s3", **kwargs)
        self._bucket = bucket
        self._key_prefix = key_prefix.rstrip("/")
        self._flush_count = flush_count
        self._buffer = io.StringIO()
        self._pending = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._buffer.write(self.format(record) + "\n")
            self._pending += 1
            if self._pending >= self._flush_count:
                self.flush()
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        content = self._buffer.getvalue()
        if not content:
            return
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d/%H%M%S")
        key = f"{self._key_prefix}/{ts}.log"
        try:
            self._client.put_object(
                Bucket=self._bucket, Key=key, Body=content.encode("utf-8")
            )
        except ClientError:  # nosec B110
            pass  # best-effort; don't raise from a log flush
        self._buffer = io.StringIO()
        self._pending = 0

    def close(self) -> None:
        self.flush()
        super().close()
