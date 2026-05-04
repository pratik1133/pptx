from typing import Protocol

from reportgen.config import settings


class PlanningModelClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a slide plan response as JSON text."""


class AnthropicPlanningClient:
    """Thin wrapper around Anthropic's Messages API for future production use."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self.model_name = model_name or settings.model_name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("Anthropic API key is not configured.")

        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError(
                "anthropic package is not installed. Add it before using the live planning client."
            ) from exc

        client = Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model_name,
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "".join(parts)
