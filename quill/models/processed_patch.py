from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProcessedPatch:
    path: str
    content: str
    is_binary: bool = False
    truncated: bool = False
    ignored_generated: bool = False
