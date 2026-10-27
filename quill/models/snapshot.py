from dataclasses import dataclass
from quill.models.repository import RepositoryInfo
from quill.models.status import GitStatus
from quill.models.change import ChangedFile
from quill.models.diff import DiffSnapshot

@dataclass(frozen=True)
class RepositorySnapshot:
    info: RepositoryInfo
    status: GitStatus
    changed_files: tuple[ChangedFile, ...]
    diff: DiffSnapshot
