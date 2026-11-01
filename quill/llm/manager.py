from quill.config.exceptions import ConfigError
from quill.config.models import QuillSettings
from quill.llm.errors import ConfigurationProviderError, TransientProviderError
from quill.llm.gemini import GeminiProvider
from quill.llm.ollama import OllamaProvider
from quill.models.patch import GenerationResult, ProviderName


class LLMManager:
    def __init__(self, settings: QuillSettings) -> None:
        self.settings = settings
        gemini = GeminiProvider(
            api_key=settings.secrets.google_api_key,
            model=settings.llm.gemini_model,
            retries=settings.llm.retries,
        )
        ollama = OllamaProvider(model=settings.llm.ollama_model, host=settings.llm.ollama_host)
        if settings.llm.default_model.lower() == "ollama":
            self.primary, self.fallback = ollama, gemini
            self.primary_name, self.fallback_name = ProviderName.OLLAMA, ProviderName.GEMINI
        else:
            self.primary, self.fallback = gemini, ollama
            self.primary_name, self.fallback_name = ProviderName.GEMINI, ProviderName.OLLAMA

    def generate(self, prompt: str) -> GenerationResult:
        try:
            message = self.primary.generate(prompt)
            return GenerationResult(message, self.primary_name)
        except (ConfigurationProviderError, ConfigError):
            raise
        except TransientProviderError as exc:
            try:
                message = self.fallback.generate(prompt)
            except Exception as fallback_exc:
                raise TransientProviderError(
                    f"{self.primary_name.value} failed temporarily; "
                    f"{self.fallback_name.value} fallback failed: {fallback_exc}"
                ) from exc
            return GenerationResult(message, self.fallback_name, fallback_used=True)
