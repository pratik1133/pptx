import json
import urllib.error
import urllib.request
from typing import Protocol

from reportgen.config import settings


class PlanningModelClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a slide plan response as JSON text."""


class OpenRouterPlanningClient:
    """Thin wrapper around OpenRouter API to access models like Claude."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        self.model_name = model_name or settings.model_name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OpenRouter API key is not configured.")

        # Attempt to use the openai package if installed
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except ImportError:
            pass

        # Fallback to direct HTTP request using urllib
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/pptx-research-report", # Fallback referer
            "X-Title": "PPTX Research Report Generator",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        req = urllib.request.Request(url, json.dumps(data).encode("utf-8"), headers)
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8")
            raise RuntimeError(f"OpenRouter API error: {exc.code} - {error_body}") from exc
