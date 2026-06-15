from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestAIClientInit(unittest.TestCase):
    @patch("aicore.client.AnthropicProvider")
    def test_anthropic_provider_created(self, mock_cls):
        from aicore import AIClient

        AIClient(provider="anthropic", model="claude-sonnet-4", api_key="sk-ant-key")
        mock_cls.assert_called_once_with(api_key="sk-ant-key", model="claude-sonnet-4")

    @patch("aicore.client.BedrockProvider")
    def test_bedrock_provider_created_role_auth(self, mock_cls):
        from aicore import AIClient

        AIClient(
            provider="bedrock", model="anthropic.claude-3-5-sonnet", region="eu-west-2"
        )
        mock_cls.assert_called_once_with(
            model="anthropic.claude-3-5-sonnet",
            region="eu-west-2",
            auth_mode="role",
            iam_key="",
            iam_secret="",
        )

    @patch("aicore.client.BedrockProvider")
    def test_bedrock_provider_created_user_auth(self, mock_cls):
        from aicore import AIClient

        AIClient(
            provider="bedrock",
            model="anthropic.claude-3-5-sonnet",
            region="us-east-1",
            auth_mode="user",
            iam_key="AKIAIOSFODNN7EXAMPLE",
            iam_secret="secret",
        )
        mock_cls.assert_called_once_with(
            model="anthropic.claude-3-5-sonnet",
            region="us-east-1",
            auth_mode="user",
            iam_key="AKIAIOSFODNN7EXAMPLE",
            iam_secret="secret",
        )

    def test_unknown_provider_raises(self):
        from aicore import AIClient

        with self.assertRaises(ValueError):
            AIClient(provider="openai", model="gpt-4")


class TestAIClientComplete(unittest.TestCase):
    @patch("aicore.client.AnthropicProvider")
    def test_complete_delegates_to_backend(self, mock_cls):
        from aicore import AIClient

        mock_backend = MagicMock()
        mock_backend.complete.return_value = "LABEL_RESULT"
        mock_cls.return_value = mock_backend

        client = AIClient(provider="anthropic", model="claude-sonnet-4", api_key="key")
        result = client.complete("my prompt", max_tokens=256)

        mock_backend.complete.assert_called_once_with("my prompt", max_tokens=256)
        self.assertEqual(result, "LABEL_RESULT")

    @patch("aicore.client.AnthropicProvider")
    def test_complete_uses_default_max_tokens(self, mock_cls):
        from aicore import AIClient

        mock_backend = MagicMock()
        mock_backend.complete.return_value = "RESULT"
        mock_cls.return_value = mock_backend

        client = AIClient(provider="anthropic", model="claude-sonnet-4", api_key="key")
        client.complete("prompt")

        mock_backend.complete.assert_called_once_with("prompt", max_tokens=512)
