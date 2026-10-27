from pathlib import Path

from git import InvalidGitRepositoryError, Repo

from quill.models.repository import RepositoryInfo


class Repository:
    def __init__(self, path: str | Path = ".") -> None:
        try:
            #Check if git repo is present or not
            self.repo = Repo(Path(path).resolve(), search_parent_directories=True)
        except (InvalidGitRepositoryError, OSError) as exc:
            raise ValueError("This directory is not inside a Git repository.") from exc
        self.root = Path(self.repo.working_tree_dir or self.repo.git_dir).resolve()

    def info(self) -> RepositoryInfo:
        try:
            #To get the active current branch of current git repo
            branch = self.repo.active_branch.name
        except TypeError:
            branch = "detached HEAD"
        try:
            head = self.repo.head.commit.hexsha[:8] if self.repo.head.is_valid() else "no commits yet"
        except (ValueError, TypeError):
            head = "no commits yet"
        return RepositoryInfo(self.root.name, self.root, branch, head)
