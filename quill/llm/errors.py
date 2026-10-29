class ProviderError(RuntimeError):
    """Base error for provider failures."""


class TransientProviderError(ProviderError):
    """A temporary error for which retry or fallback is appropriate."""


class ConfigurationProviderError(ProviderError):
    """An error that fallback cannot remedy."""
