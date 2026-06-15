from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch


class TestAnthropicProvider(unittest.TestCase):
    @patch("aicore.providers.anthropic.anthropic.Anthropic")
    def test_complete_returns_stripped_text(self, mock_anthropic_cls):
        from aicore.providers.anthropic import AnthropicProvider

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="  MY_LABEL  ")]
        )

        provider = AnthropicProvider(api_key="sk-ant-key", model="claude-sonnet-4")
        result = provider.complete("prompt", max_tokens=100)

        mock_client.messages.create.assert_called_once_with(
            model="claude-sonnet-4",
            max_tokens=100,
            messages=[{"role": "user", "content": "prompt"}],
        )
        self.assertEqual(result, "MY_LABEL")

    @patch("aicore.providers.anthropic.anthropic.Anthropic")
    def test_client_initialised_with_api_key(self, mock_anthropic_cls):
        from aicore.providers.anthropic import AnthropicProvider

        AnthropicProvider(api_key="sk-ant-test", model="model")
        mock_anthropic_cls.assert_called_once_with(api_key="sk-ant-test")


class TestBedrockProvider(unittest.TestCase):
    @patch("aicore.providers.bedrock.boto3.client")
    def test_complete_returns_stripped_text(self, mock_boto_client):
        from aicore.providers.bedrock import BedrockProvider

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        body_bytes = json.dumps({"content": [{"text": "  BEDROCK_LABEL  "}]}).encode()
        mock_client.invoke_model.return_value = {
            "body": MagicMock(read=lambda: body_bytes)
        }

        provider = BedrockProvider(
            model="anthropic.claude-3-5-sonnet", region="eu-west-2"
        )
        result = provider.complete("prompt", max_tokens=200)

        self.assertEqual(result, "BEDROCK_LABEL")
        call_kwargs = mock_client.invoke_model.call_args[1]
        self.assertEqual(call_kwargs["modelId"], "anthropic.claude-3-5-sonnet")
        body = json.loads(call_kwargs["body"])
        self.assertEqual(body["max_tokens"], 200)
        self.assertEqual(body["messages"][0]["content"], "prompt")

    @patch("aicore.providers.bedrock.boto3.client")
    def test_role_auth_does_not_pass_credentials(self, mock_boto_client):
        from aicore.providers.bedrock import BedrockProvider

        BedrockProvider(model="model", region="us-east-1", auth_mode="role")
        _, kwargs = mock_boto_client.call_args
        self.assertNotIn("aws_access_key_id", kwargs)
        self.assertNotIn("aws_secret_access_key", kwargs)

    @patch("aicore.providers.bedrock.boto3.client")
    def test_user_auth_passes_credentials(self, mock_boto_client):
        from aicore.providers.bedrock import BedrockProvider

        BedrockProvider(
            model="model",
            region="us-east-1",
            auth_mode="user",
            iam_key="AKIAIOSFODNN7EXAMPLE",
            iam_secret="wJalrXUtnFEMI",
        )
        _, kwargs = mock_boto_client.call_args
        self.assertEqual(kwargs["aws_access_key_id"], "AKIAIOSFODNN7EXAMPLE")
        self.assertEqual(kwargs["aws_secret_access_key"], "wJalrXUtnFEMI")
