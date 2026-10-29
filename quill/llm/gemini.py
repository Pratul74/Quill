import os
import time

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
            from google import genai
            from google.genai import errors
        except ImportError as exc:
            raise ConfigurationProviderError("Install Quill's Gemini dependency to use Gemini.") from exc
        client = genai.Client(api_key=self.api_key)
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = client.models.generate_content(model=self.model, contents=prompt)
                if not response.text:
                    raise ProviderError("Gemini returned an empty response.")
                return response.text
            except errors.ClientError as exc:
                if getattr(exc, "code", None) in (401, 403):
                    raise ConfigurationProviderError(f"Gemini authentication failed: {exc}") from exc
                if getattr(exc, "code", None) != 429:
                    raise ProviderError(f"Gemini request failed: {exc}") from exc
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(2**attempt, 4))
            except errors.ServerError as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(2**attempt, 4))
            except errors.APIError as exc:
                if getattr(exc, "code", None) in (401, 403):
                    raise ConfigurationProviderError(f"Gemini authentication failed: {exc}") from exc
                code = getattr(exc, "code", None)
                if code == 429 or (code is not None and code >= 500) or code is None:
                    last_error = exc
                    if attempt < self.retries:
                        time.sleep(min(2**attempt, 4))
                    continue
                raise ProviderError(f"Gemini request failed: {exc}") from exc
            except ProviderError:
                raise
            except Exception as exc:
                raise ProviderError(f"Gemini request failed: {exc}") from exc
        raise TransientProviderError(f"Gemini {self.model} is temporarily unavailable: {last_error}")
