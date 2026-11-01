from quill.config.exceptions import ConfigError
from quill.config.models import QuillSettings
from quill.llm.errors import ConfigurationProviderError, TransientProviderError
from quill.llm.gemini import GeminiProvider
from quill.llm.openai import OpenAIProvider
from quill.llm.anthropic import AnthropicProvider
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
        providers = {
            ProviderName.GEMINI: gemini,
            ProviderName.OPENAI: OpenAIProvider(settings.secrets.openai_api_key or settings.secrets.provider_api_keys.get("openai"), settings.llm.openai_model),
            ProviderName.ANTHROPIC: AnthropicProvider(settings.secrets.anthropic_api_key or settings.secrets.provider_api_keys.get("anthropic"), settings.llm.anthropic_model),
            ProviderName.OLLAMA: OllamaProvider(model=settings.llm.ollama_model, host=settings.llm.ollama_host),
        }
        self.primary_name = ProviderName(settings.llm.default_model.lower())
        self.primary = providers[self.primary_name]
        self.fallback_name = ProviderName.OLLAMA if self.primary_name != ProviderName.OLLAMA else ProviderName.GEMINI
        self.fallback = providers[self.fallback_name]

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
