import logging as stdlib_logging
import re
from unittest.mock import MagicMock, patch

import pytest
from awscore.logging import S3LogHandler
from botocore.exceptions import ClientError


def _make_handler(
    mock_s3_client=None, *, bucket="test-bucket", key_prefix="logs", flush_count=100
) -> S3LogHandler:
    if mock_s3_client is None:
        mock_s3_client = MagicMock()
    with patch("awscore.logging.boto3.client", return_value=mock_s3_client):
        return S3LogHandler(
            bucket=bucket,
            key_prefix=key_prefix,
            region="us-east-1",
            flush_count=flush_count,
        )


def _make_record(message: str = "test message") -> stdlib_logging.LogRecord:
    return stdlib_logging.LogRecord(
        name="test",
        level=stdlib_logging.INFO,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestS3LogHandlerInit:
    @pytest.fixture(autouse=True)
    def _clear_env(self, monkeypatch):
        monkeypatch.delenv("AWS_ENDPOINT", raising=False)

    def test_region_only(self):
        with patch("awscore.logging.boto3.client") as mock_client:
            S3LogHandler(bucket="b", key_prefix="k", region="eu-west-1")
        mock_client.assert_called_once_with("s3", region_name="eu-west-1")

    def test_credentials_included_when_both_provided(self):
        with patch("awscore.logging.boto3.client") as mock_client:
            S3LogHandler(
                bucket="b",
                key_prefix="k",
                region="us-east-1",
                access_key="AK",
                secret_key="SK",
            )
        args, kwargs = mock_client.call_args
        assert kwargs["aws_access_key_id"] == "AK"
        assert kwargs["aws_secret_access_key"] == "SK"

    def test_explicit_endpoint_url_used(self):
        with patch("awscore.logging.boto3.client") as mock_client:
            S3LogHandler(
                bucket="b",
                key_prefix="k",
                region="us-east-1",
                endpoint_url="http://localhost:4566",
            )
        args, kwargs = mock_client.call_args
        assert kwargs["endpoint_url"] == "http://localhost:4566"

    def test_falls_back_to_aws_endpoint_env_var(self, monkeypatch):
        monkeypatch.setenv("AWS_ENDPOINT", "http://localstack:4566")
        with patch("awscore.logging.boto3.client") as mock_client:
            S3LogHandler(bucket="b", key_prefix="k", region="us-east-1")
        args, kwargs = mock_client.call_args
        assert kwargs["endpoint_url"] == "http://localstack:4566"

    def test_strips_trailing_slash_from_key_prefix(self):
        handler = _make_handler(key_prefix="logs/app/")
        assert handler._key_prefix == "logs/app"

    def test_strips_multiple_trailing_slashes(self):
        handler = _make_handler(key_prefix="logs/app///")
        assert handler._key_prefix == "logs/app"

    def test_default_flush_count_is_100(self):
        handler = _make_handler()
        assert handler._flush_count == 100

    def test_custom_flush_count_respected(self):
        handler = _make_handler(flush_count=25)
        assert handler._flush_count == 25

    def test_initial_pending_count_is_zero(self):
        handler = _make_handler()
        assert handler._pending == 0

    def test_initial_buffer_is_empty(self):
        handler = _make_handler()
        assert handler._buffer.getvalue() == ""


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------


class TestS3LogHandlerEmit:
    def test_writes_formatted_record_and_newline_to_buffer(self):
        handler = _make_handler(flush_count=100)
        handler.emit(_make_record("hello world"))
        assert "hello world\n" in handler._buffer.getvalue()

    def test_increments_pending_count_on_each_emit(self):
        handler = _make_handler(flush_count=100)
        handler.emit(_make_record())
        assert handler._pending == 1
        handler.emit(_make_record())
        assert handler._pending == 2

    def test_does_not_flush_below_flush_count(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client, flush_count=3)
        handler.emit(_make_record())
        handler.emit(_make_record())
        mock_client.put_object.assert_not_called()

    def test_flushes_when_pending_reaches_flush_count(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client, flush_count=2)
        handler.emit(_make_record("first"))
        handler.emit(_make_record("second"))
        mock_client.put_object.assert_called_once()

    def test_calls_handle_error_on_exception_during_emit(self):
        handler = _make_handler(flush_count=100)
        record = _make_record()
        with patch.object(handler, "format", side_effect=Exception("format failed")):
            with patch.object(handler, "handleError") as mock_handle_error:
                handler.emit(record)
        mock_handle_error.assert_called_once_with(record)


# ---------------------------------------------------------------------------
# flush
# ---------------------------------------------------------------------------


class TestS3LogHandlerFlush:
    def test_no_op_when_buffer_is_empty(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client)
        handler.flush()
        mock_client.put_object.assert_not_called()

    def test_uploads_buffer_content_to_s3(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client)
        handler._buffer.write("log line\n")
        handler._pending = 1
        handler.flush()
        mock_client.put_object.assert_called_once()

    def test_s3_key_matches_expected_pattern(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client, key_prefix="myapp/logs")
        handler._buffer.write("log line\n")
        handler._pending = 1
        handler.flush()

        kwargs = mock_client.put_object.call_args.kwargs
        assert re.match(r"myapp/logs/\d{4}/\d{2}/\d{2}/\d{6}\.log$", kwargs["Key"])

    def test_content_is_utf8_encoded_bytes(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client)
        handler._buffer.write("log line\n")
        handler._pending = 1
        handler.flush()

        kwargs = mock_client.put_object.call_args.kwargs
        assert kwargs["Body"] == b"log line\n"
        assert kwargs["Bucket"] == "test-bucket"

    def test_resets_buffer_to_empty_after_flush(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client)
        handler._buffer.write("log line\n")
        handler._pending = 1
        handler.flush()
        assert handler._buffer.getvalue() == ""

    def test_resets_pending_count_to_zero_after_flush(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client)
        handler._buffer.write("log line\n")
        handler._pending = 5
        handler.flush()
        assert handler._pending == 0

    def test_swallows_client_error_silently(self):
        mock_client = MagicMock()
        mock_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": ""}}, "PutObject"
        )
        handler = _make_handler(mock_client)
        handler._buffer.write("log line\n")
        handler._pending = 1
        handler.flush()  # must not raise


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestS3LogHandlerClose:
    def test_flush_called_during_close(self):
        handler = _make_handler()
        with patch.object(handler, "flush") as mock_flush:
            handler.close()
        mock_flush.assert_called_once()

    def test_close_drains_non_empty_buffer_to_s3(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client)
        handler._buffer.write("final log\n")
        handler._pending = 1
        handler.close()
        mock_client.put_object.assert_called_once()

    def test_close_on_empty_buffer_does_not_upload(self):
        mock_client = MagicMock()
        handler = _make_handler(mock_client)
        handler.close()
        mock_client.put_object.assert_not_called()
