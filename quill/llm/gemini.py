import os

from langchain_google_genai import ChatGoogleGenerativeAI

from quill.llm.errors import ConfigurationProviderError, ProviderError, TransientProviderError
from quill.llm.provider import LLMProvider
from quill.models.config import QuillConfig


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, retries: int = 2) -> None:
        config = QuillConfig(retries=retries)
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = config.gemini_model
        self.retries = config.retries

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ConfigurationProviderError("GOOGLE_API_KEY is not set.")
        try:
            model = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key,
                max_retries=self.retries,
                temperature=0.2,
            )
            response = model.invoke(prompt)
            content = response.content
            if isinstance(content, str) and content.strip():
                return content
            raise ProviderError("Gemini returned an empty response.")
        except ProviderError:
            raise
        except Exception as exc:
            text = str(exc)
            lower_text = text.lower()
            if "api key" in lower_text or "permission_denied" in lower_text or "unauthorized" in lower_text:
                raise ConfigurationProviderError(f"Gemini authentication failed: {text}") from exc
            status_code = getattr(exc, "status_code", None)
            response = getattr(exc, "response", None)
            status_code = status_code or getattr(response, "status_code", None)
            temporary_status = any(code in lower_text for code in ("429", "500", "502", "503", "504"))
            if (
                status_code == 429
                or (status_code is not None and status_code >= 500)
                or temporary_status
                or isinstance(exc, (TimeoutError, ConnectionError))
            ):
                raise TransientProviderError(f"Gemini {self.model} is temporarily unavailable: {text}") from exc
            raise ProviderError(f"Gemini request failed: {text}") from exc
