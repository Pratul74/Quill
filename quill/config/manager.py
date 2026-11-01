"""Merge global, project, environment, and CLI configuration layers."""

import os
from pathlib import Path
from typing import Mapping

from quill.config import paths
from quill.config.exceptions import InvalidConfigError
from quill.config.loader import ConfigLoader
from quill.config.models import AppConfig, LLMConfig, QuillSettings, SecretsConfig


class ConfigManager:
    """Single configuration entry point, instantiated by the CLI and injected."""

    def __init__(
        self,
        directory: Path | None = None,
        environ: Mapping[str, str] | None = None,
        loader: ConfigLoader | None = None,
    ) -> None:
        self.directory = directory or paths.config_directory()
        self.environ = environ if environ is not None else os.environ
        self.loader = loader or ConfigLoader()

    def load(self, project_root: Path | None = None,
             cli_overrides: Mapping[str, object] | None = None) -> QuillSettings:
        """Resolve preferences and secrets in documented precedence order."""
        global_config = self.loader.load_app(self.directory / "config.toml")
        values = global_config.model_dump()

        if project_root is not None:
            project = self.loader.load_project_preferences(paths.project_config_file(project_root))
            values.update(project.model_dump(exclude_unset=True, exclude_none=True))

        secrets = self.loader.load_secrets(self.directory / "secrets.toml").model_dump()
        values.update(self._environment_preferences())
        env_secrets = self._environment_secrets()
        secrets["provider_api_keys"].update(env_secrets.pop("provider_api_keys", {}))
        secrets.update(env_secrets)
        if cli_overrides:
            values.update(cli_overrides)

        app = AppConfig.model_validate(values)
        llm = LLMConfig.model_validate(app.model_dump(include={
            "default_model", "gemini_model", "openai_model", "anthropic_model", "ollama_model", "ollama_host", "retries",
        }))
        return QuillSettings(app=app, llm=llm, secrets=SecretsConfig.model_validate(secrets))

    def _environment_preferences(self) -> dict[str, object]:
        mapping = {
            "QUILL_DEFAULT_MODEL": "default_model",
            "QUILL_COMMIT_STYLE": "commit_style",
            "QUILL_LANGUAGE": "language",
            "QUILL_EDITOR": "editor",
            "QUILL_GEMINI_MODEL": "gemini_model",
            "QUILL_OPENAI_MODEL": "openai_model",
            "QUILL_ANTHROPIC_MODEL": "anthropic_model",
            "QUILL_RETRIES": "retries",
        }
        values: dict[str, object] = {
            target: self.environ[source]
            for source, target in mapping.items()
            if source in self.environ
        }
        if "EDITOR" in self.environ and "QUILL_EDITOR" not in self.environ:
            values["editor"] = self.environ["EDITOR"]
        if "QUILL_CONFIRM_BEFORE_COMMIT" in self.environ:
            values["confirm_before_commit"] = self._as_bool(self.environ["QUILL_CONFIRM_BEFORE_COMMIT"])
        for source, target in (("OLLAMA_MODEL", "ollama_model"), ("QUILL_OLLAMA_MODEL", "ollama_model"),
                               ("OLLAMA_HOST", "ollama_host"), ("QUILL_OLLAMA_HOST", "ollama_host")):
            if source in self.environ:
                values[target] = self.environ[source]
        return values

    def _environment_secrets(self) -> dict[str, object]:
        secrets: dict[str, object] = {}
        provider_keys = {}
        for provider in ("openai", "anthropic"):
            for variable in (f"{provider.upper()}_API_KEY", f"QUILL_{provider.upper()}_API_KEY"):
                if variable in self.environ:
                    provider_keys[provider] = self.environ[variable]
        if provider_keys:
            secrets["provider_api_keys"] = provider_keys
        for variable in ("GOOGLE_API_KEY", "QUILL_GOOGLE_API_KEY"):
            if variable in self.environ:
                secrets["google_api_key"] = self.environ[variable]
        return secrets

    @staticmethod
    def _as_bool(value: str) -> bool:
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise InvalidConfigError("QUILL_CONFIRM_BEFORE_COMMIT must be true or false.")
