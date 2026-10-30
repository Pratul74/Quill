import os

from langchain_ollama import ChatOllama

from quill.llm.errors import ProviderError
from quill.llm.provider import LLMProvider
from quill.models.config import QuillConfig


class OllamaProvider(LLMProvider):
    def __init__(self, model: str | None = None, host: str | None = None) -> None:
        config = QuillConfig(
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )
        self.model = model or config.ollama_model
        self.host = host or config.ollama_host

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
