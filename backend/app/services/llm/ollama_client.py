from typing import Any

import requests

from app.core.config import get_settings
from app.services.llm.base import BaseLLMClient


class OllamaClient(BaseLLMClient):
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_text(self, prompt: str) -> str:
        payload = {
            "model": self.settings.ollama_model,
            "messages": [
                {"role": "system", "content": "你是一个供应链库存补货分析助手。"},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        response = requests.post(
            f"{self.settings.ollama_base_url}/api/chat",
            json=payload,
            timeout=self.settings.llm_timeout_seconds,
        )
        if response.ok:
            data = response.json()
            return data.get("message", {}).get("content", "")
        fallback = requests.post(
            f"{self.settings.ollama_base_url}/api/generate",
            json={"model": self.settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=self.settings.llm_timeout_seconds,
        )
        fallback.raise_for_status()
        return fallback.json().get("response", "")

    def generate_json(self, prompt: str, json_schema: dict | None = None) -> dict[str, Any]:
        return {"text": self.generate_text(prompt), "json_schema": json_schema or {}}
