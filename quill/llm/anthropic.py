from langchain_anthropic import ChatAnthropic
from anthropic import APIConnectionError, InternalServerError, RateLimitError

from quill.config.exceptions import MissingAPIKeyError
from quill.llm.errors import ConfigurationProviderError, ProviderError, TransientProviderError
from quill.llm.provider import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key, self.model = api_key, model

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise MissingAPIKeyError("Anthropic requires an API key. Add anthropic_api_key to secrets.toml or set QUILL_ANTHROPIC_API_KEY.")
        try:
            result = ChatAnthropic(model=self.model, api_key=self.api_key, temperature=0.2).invoke(prompt)
            text = result.content if isinstance(result.content, str) else "".join(
                part.get("text", "") for part in result.content if isinstance(part, dict)
            )
            if not text.strip():
                raise ProviderError("Anthropic returned an empty response.")
            return text.strip()
        except ProviderError:
            raise
        except (APIConnectionError, InternalServerError, RateLimitError) as exc:
            raise TransientProviderError(f"Anthropic is temporarily unavailable: {exc}") from exc
        except Exception as exc:
            raise ConfigurationProviderError(f"Anthropic request failed for {self.model}: {exc}") from exc
