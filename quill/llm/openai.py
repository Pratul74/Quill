from langchain_openai import ChatOpenAI
from openai import APIConnectionError, InternalServerError, RateLimitError

from quill.config.exceptions import MissingAPIKeyError
from quill.llm.errors import ConfigurationProviderError, ProviderError, TransientProviderError
from quill.llm.provider import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key, self.model = api_key, model

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise MissingAPIKeyError("OpenAI requires an API key. Add openai_api_key to secrets.toml or set QUILL_OPENAI_API_KEY.")
        try:
            result = ChatOpenAI(model=self.model, api_key=self.api_key, temperature=0.2).invoke(prompt)
            text = result.content if isinstance(result.content, str) else "".join(
                part.get("text", "") for part in result.content if isinstance(part, dict)
            )
            if not text.strip():
                raise ProviderError("OpenAI returned an empty response.")
            return text.strip()
        except ProviderError:
            raise
        except (APIConnectionError, InternalServerError, RateLimitError) as exc:
            raise TransientProviderError(f"OpenAI is temporarily unavailable: {exc}") from exc
        except Exception as exc:
            raise ConfigurationProviderError(f"OpenAI request failed for {self.model}: {exc}") from exc
