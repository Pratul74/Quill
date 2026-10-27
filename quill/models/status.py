from dataclasses import dataclass
from enum import Enum


class RepoOperation(str, Enum):
    NONE = "none"
    MERGE = "merge"
    REBASE = "rebase"
    CHERRY_PICK = "cherry-pick"
    REVERT = "revert"


@dataclass(frozen=True, slots=True)
class GitStatus:
    has_staged: bool
    has_unstaged: bool
    has_untracked: bool
    has_conflicts: bool
    is_detached_head: bool
    has_commits: bool
    operation: RepoOperation = RepoOperation.NONE

    @property
    def is_clean(self) -> bool:
        return not (self.has_staged or self.has_unstaged or self.has_untracked)

    @property
    def can_create_messages(self) -> bool:
        return self.has_staged and not self.has_conflicts
