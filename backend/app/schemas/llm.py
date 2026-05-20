from pydantic import BaseModel


class LLMStatusResponse(BaseModel):
    provider: str
    model: str | None = None
    available: bool
    base_url: str | None = None
    key_configured: bool | None = None
