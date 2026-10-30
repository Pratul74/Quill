import os

from google.api_core import exceptions as gexc
from langchain_google_genai import ChatGoogleGenerativeAI

from quill.llm.errors import ConfigurationProviderError, ProviderError, TransientProviderError
from quill.llm.provider import LLMProvider
from quill.models.config import QuillConfig


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, retries: int = 2) -> None:
        config = QuillConfig()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = config.gemini_model
        self.retries = retries
        self._client: ChatGoogleGenerativeAI | None = None

    def _get_client(self) -> ChatGoogleGenerativeAI:
        if not self.api_key:
            raise ConfigurationProviderError("GOOGLE_API_KEY is not set.")
        if self._client is None:
            self._client = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key,
                max_retries=self.retries,
                temperature=0.2,
            )
        return self._client

    @staticmethod
    def _extract_text(content) -> str:
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
        client = self._get_client()
        try:
            result = client.invoke(prompt)
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

        text = self._extract_text(result.content).strip()
        if not text:
            reason = getattr(result, "response_metadata", {}).get("finish_reason")
            raise ProviderError(f"Gemini returned an empty response (finish_reason={reason}).")
        return text
