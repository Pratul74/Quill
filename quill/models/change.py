from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChangedFile:
    path: str
    change_type: str
    additions: int = 0
    deletions: int = 0
