import tomllib
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from quill.config.exceptions import InvalidConfigError
from quill.config.models import AppConfig, ProjectPreferences, SecretsConfig

ModelT = TypeVar("ModelT", bound=BaseModel)


class ConfigLoader:
    def load_app(self, path: Path) -> AppConfig:
        if not path.exists():
            return AppConfig()
        return self._validate(path, AppConfig)

    def load_secrets(self, path: Path) -> SecretsConfig:
        if not path.exists():
            return SecretsConfig()
        return self._validate(path, SecretsConfig)

    def load_project_preferences(self, path: Path) -> ProjectPreferences:
        if not path.exists():
            return ProjectPreferences()
        return self._validate(path, ProjectPreferences)

    @staticmethod
    def _validate(path: Path, model: type[ModelT]) -> ModelT:
        try:
            with path.open("rb") as source:
                values = tomllib.load(source)
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            raise InvalidConfigError(f"Invalid Quill configuration at {path}: {exc}") from exc
        try:
            return model.model_validate(values)
        except ValidationError as exc:
            details = "; ".join(error["msg"] for error in exc.errors(include_input=False))
            raise InvalidConfigError(f"Invalid Quill configuration at {path}: {details}") from exc
