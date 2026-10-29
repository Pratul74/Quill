from quill.llm.errors import ConfigurationProviderError, TransientProviderError
from quill.llm.gemini import GeminiProvider
from quill.llm.ollama import OllamaProvider
from quill.llm.provider import LLMProvider
from quill.models.patch import GenerationResult, ProviderName


class LLMManager:
    def __init__(self, primary: LLMProvider | None = None, fallback: LLMProvider | None = None) -> None:
        self.primary = primary or GeminiProvider()
        self.fallback = fallback or OllamaProvider()

    def generate(self, prompt: str) -> GenerationResult:
        try:
            message = self.primary.generate(prompt)
            return GenerationResult(message, ProviderName.GEMINI)
        except ConfigurationProviderError:
            raise
        except TransientProviderError as exc:
            try:
                message = self.fallback.generate(prompt)
            except Exception as fallback_exc:
                raise TransientProviderError(f"Gemini failed temporarily; Ollama fallback failed: {fallback_exc}") from exc
            return GenerationResult(message, ProviderName.OLLAMA, fallback_used=True)
