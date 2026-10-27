from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiffSnapshot:
    text: str
    files: tuple[str, ...]
    additions: int
    deletions: int
