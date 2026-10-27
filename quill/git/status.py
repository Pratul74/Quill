from git import Repo

from quill.models.status import GitStatus


class StatusService:
    def __init__(self, repo: Repo) -> None:
        self.repo = repo

    def get_status(self) -> GitStatus:
        staged = self.repo.git.diff("--cached", "--name-only", "-z").split("\0")
        try:
            detached = self.repo.head.is_detached
            has_commits = self.repo.head.is_valid()
        except (ValueError, TypeError):
            detached, has_commits = False, False
        return GitStatus(bool([p for p in staged if p]), bool(self.repo.index.diff(None)),
                         bool(self.repo.untracked_files), bool(self.repo.index.unmerged_blobs()),
                         detached, has_commits)
