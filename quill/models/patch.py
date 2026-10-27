from dataclasses import dataclass
from enum import Enum


class ProviderName(str, Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"


@dataclass(frozen=True, slots=True)
class GenerationResult:
    message: str
    provider: ProviderName
    fallback_used: bool = False
