from git import Repo
from quill.git.diff import DiffService
from quill.git.repository import Repository
from quill.git.status import StatusService
from quill.models.snapshot import RepositorySnapshot


def inspect_repository(path: str = ".") -> tuple[Repo, RepositorySnapshot]:
    repository = Repository(path)
    repo = repository.repo
    diff_service = DiffService(repo)
    diff = diff_service.get_staged_diff()
    snapshot = RepositorySnapshot(repository.info(), StatusService(repo).get_status(),
                                  diff_service.get_changed_files(), diff)
    return repo, snapshot
