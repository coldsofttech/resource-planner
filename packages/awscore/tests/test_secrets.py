import logging
from unittest.mock import patch

import pytest
from awscore.secrets import SecretsManager
from botocore.exceptions import ClientError


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Operation")


def _make_manager() -> SecretsManager:
    with patch("awscore.secrets.boto3.client"):
        return SecretsManager(region="us-east-1")


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestSecretsManagerInit:
    @pytest.fixture(autouse=True)
    def _clear_env(self, monkeypatch):
        monkeypatch.delenv("AWS_ENDPOINT", raising=False)

    def test_region_only(self):
        with patch("awscore.secrets.boto3.client") as mock_client:
            SecretsManager(region="eu-west-1")
        mock_client.assert_called_once_with("secretsmanager", region_name="eu-west-1")

    def test_credentials_included_when_both_provided(self):
        with patch("awscore.secrets.boto3.client") as mock_client:
            SecretsManager(region="us-east-1", access_key="AK", secret_key="SK")
        args, kwargs = mock_client.call_args
        assert kwargs["aws_access_key_id"] == "AK"
        assert kwargs["aws_secret_access_key"] == "SK"

    def test_credentials_omitted_when_only_access_key_provided(self):
        with patch("awscore.secrets.boto3.client") as mock_client:
            SecretsManager(region="us-east-1", access_key="AK")
        args, kwargs = mock_client.call_args
        assert "aws_access_key_id" not in kwargs
        assert "aws_secret_access_key" not in kwargs

    def test_credentials_omitted_when_only_secret_key_provided(self):
        with patch("awscore.secrets.boto3.client") as mock_client:
            SecretsManager(region="us-east-1", secret_key="SK")
        args, kwargs = mock_client.call_args
        assert "aws_access_key_id" not in kwargs
        assert "aws_secret_access_key" not in kwargs

    def test_explicit_endpoint_url_used(self):
        with patch("awscore.secrets.boto3.client") as mock_client:
            SecretsManager(region="us-east-1", endpoint_url="http://localhost:4566")
        args, kwargs = mock_client.call_args
        assert kwargs["endpoint_url"] == "http://localhost:4566"

    def test_falls_back_to_aws_endpoint_env_var(self, monkeypatch):
        monkeypatch.setenv("AWS_ENDPOINT", "http://localstack:4566")
        with patch("awscore.secrets.boto3.client") as mock_client:
            SecretsManager(region="us-east-1")
        args, kwargs = mock_client.call_args
        assert kwargs["endpoint_url"] == "http://localstack:4566"

    def test_endpoint_omitted_when_neither_arg_nor_env_var_set(self):
        with patch("awscore.secrets.boto3.client") as mock_client:
            SecretsManager(region="us-east-1")
        args, kwargs = mock_client.call_args
        assert "endpoint_url" not in kwargs


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestSecretsManagerList:
    def test_returns_empty_list_when_no_secrets_match(self):
        manager = _make_manager()
        paginator = manager._client.get_paginator.return_value
        paginator.paginate.return_value = [{"SecretList": []}]

        assert manager.list("myapp/") == []

    def test_returns_names_from_single_page(self):
        manager = _make_manager()
        paginator = manager._client.get_paginator.return_value
        paginator.paginate.return_value = [
            {"SecretList": [{"Name": "myapp/db"}, {"Name": "myapp/key"}]}
        ]

        assert manager.list("myapp/") == ["myapp/db", "myapp/key"]

    def test_aggregates_names_across_multiple_pages(self):
        manager = _make_manager()
        paginator = manager._client.get_paginator.return_value
        paginator.paginate.return_value = [
            {"SecretList": [{"Name": "myapp/a"}]},
            {"SecretList": [{"Name": "myapp/b"}, {"Name": "myapp/c"}]},
        ]

        assert manager.list("myapp/") == ["myapp/a", "myapp/b", "myapp/c"]

    def test_filters_by_prefix_in_paginator_call(self):
        manager = _make_manager()
        paginator = manager._client.get_paginator.return_value
        paginator.paginate.return_value = []

        manager.list("myapp/")

        paginator.paginate.assert_called_once_with(
            Filters=[{"Key": "name", "Values": ["myapp/"]}]
        )


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


class TestSecretsManagerGet:
    def test_returns_secret_string_value(self):
        manager = _make_manager()
        manager._client.get_secret_value.return_value = {"SecretString": "s3cr3t"}

        assert manager.get("myapp/key") == "s3cr3t"

    def test_returns_empty_string_when_secret_string_key_absent(self):
        manager = _make_manager()
        manager._client.get_secret_value.return_value = {}

        assert manager.get("myapp/key") == ""

    def test_raises_client_error_when_secret_not_found(self):
        manager = _make_manager()
        manager._client.get_secret_value.side_effect = _client_error(
            "ResourceNotFoundException"
        )

        with pytest.raises(ClientError):
            manager.get("missing/secret")

    def test_logs_error_before_reraising_client_error(self, caplog):
        manager = _make_manager()
        manager._client.get_secret_value.side_effect = _client_error(
            "ResourceNotFoundException"
        )

        with caplog.at_level(logging.ERROR, logger="awscore.secrets"):
            with pytest.raises(ClientError):
                manager.get("missing/secret")

        assert "missing/secret" in caplog.text


# ---------------------------------------------------------------------------
# put
# ---------------------------------------------------------------------------


class TestSecretsManagerPut:
    def test_creates_secret_without_description_kwarg(self):
        manager = _make_manager()
        manager.put("myapp/key", "value")
        manager._client.create_secret.assert_called_once_with(
            Name="myapp/key", SecretString="value"
        )

    def test_includes_description_when_provided(self):
        manager = _make_manager()
        manager.put("myapp/key", "value", description="My secret")
        manager._client.create_secret.assert_called_once_with(
            Name="myapp/key", SecretString="value", Description="My secret"
        )

    def test_logs_info_on_success(self, caplog):
        manager = _make_manager()
        with caplog.at_level(logging.INFO, logger="awscore.secrets"):
            manager.put("myapp/key", "value")
        assert "myapp/key" in caplog.text

    def test_raises_and_logs_on_client_error(self, caplog):
        manager = _make_manager()
        manager._client.create_secret.side_effect = _client_error(
            "ResourceExistsException"
        )

        with caplog.at_level(logging.ERROR, logger="awscore.secrets"):
            with pytest.raises(ClientError):
                manager.put("myapp/key", "value")

        assert "myapp/key" in caplog.text


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestSecretsManagerUpdate:
    def test_calls_put_secret_value_with_correct_args(self):
        manager = _make_manager()
        manager.update("myapp/key", "new_value")
        manager._client.put_secret_value.assert_called_once_with(
            SecretId="myapp/key", SecretString="new_value"
        )

    def test_logs_info_on_success(self, caplog):
        manager = _make_manager()
        with caplog.at_level(logging.INFO, logger="awscore.secrets"):
            manager.update("myapp/key", "new_value")
        assert "myapp/key" in caplog.text

    def test_raises_and_logs_on_client_error(self, caplog):
        manager = _make_manager()
        manager._client.put_secret_value.side_effect = _client_error(
            "ResourceNotFoundException"
        )

        with caplog.at_level(logging.ERROR, logger="awscore.secrets"):
            with pytest.raises(ClientError):
                manager.update("missing/key", "value")

        assert "missing/key" in caplog.text


# ---------------------------------------------------------------------------
# put_or_update
# ---------------------------------------------------------------------------


class TestSecretsManagerPutOrUpdate:
    def test_calls_update_first_and_skips_put_on_success(self):
        manager = _make_manager()
        manager.put_or_update("myapp/key", "value")
        manager._client.put_secret_value.assert_called_once()
        manager._client.create_secret.assert_not_called()

    def test_falls_back_to_put_on_resource_not_found(self):
        manager = _make_manager()
        manager._client.put_secret_value.side_effect = _client_error(
            "ResourceNotFoundException"
        )
        manager.put_or_update("myapp/key", "value")
        manager._client.create_secret.assert_called_once()

    def test_passes_description_to_put_on_fallback(self):
        manager = _make_manager()
        manager._client.put_secret_value.side_effect = _client_error(
            "ResourceNotFoundException"
        )
        manager.put_or_update("myapp/key", "value", description="my desc")
        assert (
            manager._client.create_secret.call_args.kwargs.get("Description")
            == "my desc"
        )

    def test_reraises_non_resource_not_found_client_error(self):
        manager = _make_manager()
        manager._client.put_secret_value.side_effect = _client_error(
            "AccessDeniedException"
        )

        with pytest.raises(ClientError):
            manager.put_or_update("myapp/key", "value")

        manager._client.create_secret.assert_not_called()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestSecretsManagerDelete:
    def test_deletes_without_force_by_default(self):
        manager = _make_manager()
        manager.delete("myapp/key")
        manager._client.delete_secret.assert_called_once_with(
            SecretId="myapp/key", ForceDeleteWithoutRecovery=False
        )

    def test_deletes_with_force_when_requested(self):
        manager = _make_manager()
        manager.delete("myapp/key", force=True)
        manager._client.delete_secret.assert_called_once_with(
            SecretId="myapp/key", ForceDeleteWithoutRecovery=True
        )

    def test_logs_info_on_success(self, caplog):
        manager = _make_manager()
        with caplog.at_level(logging.INFO, logger="awscore.secrets"):
            manager.delete("myapp/key")
        assert "myapp/key" in caplog.text

    def test_raises_and_logs_on_client_error(self, caplog):
        manager = _make_manager()
        manager._client.delete_secret.side_effect = _client_error(
            "ResourceNotFoundException"
        )

        with caplog.at_level(logging.ERROR, logger="awscore.secrets"):
            with pytest.raises(ClientError):
                manager.delete("missing/key")

        assert "missing/key" in caplog.text
