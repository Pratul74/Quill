"""Configuration-specific errors presented by the CLI."""


class ConfigError(Exception):
    """Base class for configuration failures."""


class ConfigNotFoundError(ConfigError):
    """A required Quill configuration file does not exist."""


class SecretsNotFoundError(ConfigError):
    """The global secrets file does not exist when explicitly required."""


class InvalidConfigError(ConfigError):
    """Configuration TOML is malformed or does not match its schema."""


class MissingAPIKeyError(ConfigError):
    """A provider requiring an API key was selected without a configured key."""
