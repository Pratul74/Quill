from pydantic import BaseModel, ConfigDict, Field


class QuillConfig(BaseModel):
    """Validated provider settings loaded from the process environment."""

    model_config = ConfigDict(frozen=True)

    gemini_model: str = "gemini-3.5-flash-lite"
    ollama_model: str = "qwen3:8b"
    ollama_host: str = "http://localhost:11434"
    retries: int = Field(default=2, ge=0, le=5)
