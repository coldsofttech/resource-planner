from __future__ import annotations

from .providers.anthropic import AnthropicProvider
from .providers.bedrock import BedrockProvider


class AIClient:
    """Unified AI client that dispatches to Anthropic or AWS Bedrock.

    Args:
        provider:   "anthropic" or "bedrock"
        model:      Model identifier string.
                    Anthropic example: "claude-sonnet-4-20250514"
                    Bedrock example:   "anthropic.claude-3-5-sonnet-20241022-v2:0"
        api_key:    Anthropic API key. Required when provider="anthropic".
        region:     AWS region. Required when provider="bedrock".
        auth_mode:  "role" (default) or "user". Only used when provider="bedrock".
        iam_key:    IAM access key ID. Required when auth_mode="user".
        iam_secret: IAM secret access key. Required when auth_mode="user".
    """

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str = "",
        region: str = "",
        auth_mode: str = "role",
        iam_key: str = "",
        iam_secret: str = "",
    ) -> None:
        backend: AnthropicProvider | BedrockProvider
        if provider == "anthropic":
            backend = AnthropicProvider(api_key=api_key, model=model)
        elif provider == "bedrock":
            backend = BedrockProvider(
                model=model,
                region=region,
                auth_mode=auth_mode,
                iam_key=iam_key,
                iam_secret=iam_secret,
            )
        else:
            raise ValueError(f"Unsupported AI provider: {provider!r}")
        self._backend = backend

    def complete(self, prompt: str, max_tokens: int = 512) -> str:
        """Send *prompt* to the configured provider and return the response text."""
        return self._backend.complete(prompt, max_tokens=max_tokens)
