import os

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
            from ollama import Client
            response = Client(host=self.host).chat(model=self.model, messages=[{"role": "user", "content": prompt}])
            content = response.message.content
            if not content:
                raise ProviderError("Ollama returned an empty response.")
            return content
        except ImportError as exc:
            raise ProviderError("Install Quill's Ollama dependency to use local fallback.") from exc
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Ollama ({self.model}) is unavailable: {exc}") from exc
