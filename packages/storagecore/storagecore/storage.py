from __future__ import annotations

import base64
import mimetypes
import os
from typing import Optional

_S3_ARN_PREFIX = "arn:aws:s3:::"

STORAGE_DATABASE = "database"
STORAGE_FILESYSTEM = "filesystem"
STORAGE_S3 = "s3"


def _guess_mime(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    """
    Return (bucket, key) from an 'aws:arn:aws:s3:::bucket/folder/file' URI.
    """
    path = uri.removeprefix("aws:").removeprefix(_S3_ARN_PREFIX)
    bucket, _, key = path.partition("/")
    return bucket, key


def _bucket_from_storage_path(storage_path: str) -> str:
    """
    Extract the S3 bucket name from an ARN storage path.
    e.g. 'arn:aws:s3:::my-bucket' → 'my-bucket'
    """
    return storage_path.removeprefix(_S3_ARN_PREFIX).split("/")[0]


def store(
    content: bytes,
    filename: str,
    folder: str,
    storage_type: str,
    storage_path: str = "",
    aws_region: str = "",
    aws_access_key: str = "",
    aws_secret_key: str = "",
    content_type: Optional[str] = None,
) -> str:
    """
    Persist *content* according to *storage_type* and return a canonical URI.

    Returned URI forms:
      database   →  data:<mime>;base64,<b64>
      filesystem →  file:<absolute-path>
      s3         →  aws:arn:aws:s3:::<bucket>/<folder>/<filename>
    """
    ct = content_type or _guess_mime(filename)

    if storage_type == STORAGE_DATABASE:
        b64 = base64.b64encode(content).decode("ascii")
        return f"data:{ct};base64,{b64}"

    if storage_type == STORAGE_FILESYSTEM:
        fallback = os.path.join(os.sep, "tmp")
        base = storage_path.rstrip(os.sep) if storage_path else fallback
        dest = os.path.join(base, folder, filename)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(content)
        return f"file:{dest}"

    if storage_type == STORAGE_S3:
        from storagecore.s3 import S3Client

        bucket = _bucket_from_storage_path(storage_path)
        key = f"{folder.strip('/')}/{filename}"
        s3 = S3Client(
            region=aws_region,
            access_key=aws_access_key,
            secret_key=aws_secret_key,
        )
        s3.put(bucket, key, content, ct)
        base_arn = storage_path.rstrip("/")
        return f"aws:{base_arn}/{key}"

    raise ValueError(f"Unknown storage_type: {storage_type!r}")


def retrieve(
    uri: str,
    aws_region: str = "",
    aws_access_key: str = "",
    aws_secret_key: str = "",
) -> bytes:
    """Return raw bytes for a stored URI."""
    if uri.startswith("data:"):
        _, data = uri.split(",", 1)
        return base64.b64decode(data)

    if uri.startswith("file:"):
        path = uri[len("file:") :]
        with open(path, "rb") as fh:
            return fh.read()

    if uri.startswith("aws:"):
        from storagecore.s3 import S3Client

        bucket, key = _parse_s3_uri(uri)
        s3 = S3Client(
            region=aws_region,
            access_key=aws_access_key,
            secret_key=aws_secret_key,
        )
        return s3.get(bucket, key)

    raise ValueError(f"Unrecognised storage URI: {uri!r}")


def delete(
    uri: str,
    aws_region: str = "",
    aws_access_key: str = "",
    aws_secret_key: str = "",
) -> None:
    """Delete the file at *uri*. No-op for data: URIs."""
    if uri.startswith("data:"):
        return

    if uri.startswith("file:"):
        path = uri[len("file:") :]
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        return

    if uri.startswith("aws:"):
        from storagecore.s3 import S3Client

        bucket, key = _parse_s3_uri(uri)
        s3 = S3Client(
            region=aws_region,
            access_key=aws_access_key,
            secret_key=aws_secret_key,
        )
        s3.delete(bucket, key)
        return

    raise ValueError(f"Unrecognised storage URI: {uri!r}")
