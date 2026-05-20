from typing import Any


class BaseLLMClient:
    def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

    def generate_json(self, prompt: str, json_schema: dict | None = None) -> dict[str, Any]:
        raise NotImplementedError
