from google.api_core import exceptions as gexc
from collections.abc import Callable
from langchain_google_genai import ChatGoogleGenerativeAI

from quill.config.exceptions import MissingAPIKeyError
from quill.llm.errors import ConfigurationProviderError, ProviderError, TransientProviderError
from quill.llm.provider import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None, model: str, retries: int = 2) -> None:
        self.api_key = api_key or None
        self.model = model
        self.retries = retries
        self._client: ChatGoogleGenerativeAI | None = None

    def _get_client(self) -> ChatGoogleGenerativeAI:
        if not self.api_key:
            raise MissingAPIKeyError(
                "Gemini requires an API key. Add google_api_key to Quill's global secrets.toml "
                "or export GOOGLE_API_KEY in your shell."
            )
        if self._client is None:
            self._client = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key,
                max_retries=self.retries,
            )
        return self._client

    @staticmethod
    def _extract_text(content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                p if isinstance(p, str) else p.get("text", "")
                for p in content
                if isinstance(p, (str, dict))
            )
        return ""

    def generate(self, prompt: str) -> str:
        return self._generate(prompt, None)

    def stream(self, prompt: str, on_token: Callable[[str], None]) -> str:
        return self._generate(prompt, on_token)

    def _generate(self, prompt: str, on_token: Callable[[str], None] | None) -> str:
        client = self._get_client()
        try:
            if on_token is None:
                result = client.invoke(prompt)
                content = result.content
                text = self._extract_text(content)
            else:
                parts = []
                for chunk in client.stream(prompt):
                    piece = self._extract_text(chunk.content)
                    if piece:
                        parts.append(piece)
                        on_token(piece)
                text = "".join(parts)
        except (gexc.Unauthenticated, gexc.PermissionDenied) as exc:
            raise ConfigurationProviderError(f"Gemini authentication failed: {exc}") from exc
        except (gexc.ResourceExhausted, gexc.ServiceUnavailable,
                gexc.DeadlineExceeded, gexc.InternalServerError,
                TimeoutError, ConnectionError) as exc:
            raise TransientProviderError(
                f"Gemini {self.model} is temporarily unavailable: {exc}"
            ) from exc
        except Exception as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc

        text = text.strip()
        if not text:
            reason = getattr(result, "response_metadata", {}).get("finish_reason")
            raise ProviderError(f"Gemini returned an empty response (finish_reason={reason}).")
        return text
