from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RepositoryInfo:
    name: str
    root_path: Path
    current_branch: str
    head_commit: str
