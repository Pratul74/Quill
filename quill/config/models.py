"""Typed configuration values; this module performs no I/O."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_model: str = "gemini"
    commit_style: str = "conventional"
    language: str = "en"
    editor: str | None = None
    confirm_before_commit: bool = True
    gemini_model: str = "gemini-3.5-flash-lite"
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-haiku-4-5-20251001"
    ollama_model: str = "qwen3:8b"
    ollama_host: str = "http://localhost:11434"
    retries: int = Field(default=2, ge=0, le=5)

    @field_validator("default_model")
    @classmethod
    def validate_default_model(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"gemini", "openai", "anthropic", "ollama"}:
            raise ValueError("default_model must be 'gemini', 'openai', 'anthropic', or 'ollama'.")
        return normalized


class ProjectPreferences(BaseModel):
    """Partial project overrides; intentionally has no secret fields."""

    model_config = ConfigDict(extra="forbid")

    default_model: str | None = None
    commit_style: str | None = None
    language: str | None = None
    editor: str | None = None
    confirm_before_commit: bool | None = None


class SecretsConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    google_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    provider_api_keys: dict[str, str] = Field(default_factory=dict)


class LLMConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    default_model: str
    gemini_model: str
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-haiku-4-5-20251001"
    ollama_model: str
    ollama_host: str
    retries: int


class QuillSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    app: AppConfig
    llm: LLMConfig
    secrets: SecretsConfig
