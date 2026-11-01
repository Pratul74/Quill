from langchain_ollama import ChatOllama

from quill.llm.errors import ProviderError
from quill.llm.provider import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, host: str) -> None:
        self.model = model
        self.host = host

    def generate(self, prompt: str) -> str:
        try:
            response = ChatOllama(model=self.model, base_url=self.host, temperature=0.2).invoke(prompt)
            content = response.content
            if not isinstance(content, str) or not content.strip():
                raise ProviderError("Ollama returned an empty response.")
            return content
        except ImportError as exc:
            raise ProviderError("Install Quill's Ollama dependency to use local fallback.") from exc
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Ollama ({self.model}) is unavailable: {exc}") from exc
