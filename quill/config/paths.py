"""Operating-system aware Quill configuration paths."""

import os
import sys
from pathlib import Path


def config_directory() -> Path:
    """Return the platform's standard per-user Quill configuration directory."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        return (Path(base) if base else Path.home() / "AppData" / "Roaming") / "quill"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "quill"
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base).expanduser() if base else Path.home() / ".config") / "quill"


def config_file() -> Path:
    return config_directory() / "config.toml"


def secrets_file() -> Path:
    return config_directory() / "secrets.toml"


def project_config_file(project_root: Path) -> Path:
    return project_root / ".quill.toml"
