"""Initialize Quill's global configuration files."""

import os
from pathlib import Path

from quill.config import paths


def initialize_config(directory: Path | None = None) -> Path:
    """Create the global config directory and starter files without overwriting."""
    root = directory or paths.config_directory()
    root.mkdir(parents=True, exist_ok=True)
    config = root / "config.toml"
    secrets = root / "secrets.toml"
    if not config.exists():
        config.write_text(
            '# Quill preferences. Secrets belong in secrets.toml.\n'
            'default_model = "gemini"\n'
            'commit_style = "conventional"\n'
            'language = "en"\n'
            'confirm_before_commit = true\n'
            'gemini_model = "gemini-3.5-flash-lite"\n'
            'openai_model = "gpt-4o-mini"\n'
            'anthropic_model = "claude-haiku-4-5-20251001"\n'
            'ollama_model = "qwen3:8b"\n'
            'ollama_host = "http://localhost:11434"\n'
            'retries = 2\n',
            encoding="utf-8",
        )
    if not secrets.exists():
        secrets.write_text(
            'google_api_key = ""\nopenai_api_key = ""\nanthropic_api_key = ""\n',
            encoding="utf-8",
        )
        try:
            os.chmod(secrets, 0o600)
        except OSError:
            pass
    return root
