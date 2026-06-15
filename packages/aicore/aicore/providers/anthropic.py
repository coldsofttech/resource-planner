from __future__ import annotations

import anthropic
from anthropic.types import TextBlock


class AnthropicProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, prompt: str, max_tokens: int = 512) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        block = next((b for b in message.content if isinstance(b, TextBlock)), None)
        return block.text.strip() if block is not None else ""
