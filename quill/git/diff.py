from git import Repo

from quill.models.change import ChangedFile
from quill.models.diff import DiffSnapshot


class DiffService:
    def __init__(self, repo: Repo) -> None:
        self.repo = repo

    def get_staged_diff(self) -> DiffSnapshot:
        files = self.get_changed_files()
        names = tuple(file.path for file in files)
        raw = self.repo.git.diff("--cached", "--no-ext-diff", "--unified=3", "--find-renames")
        return DiffSnapshot(raw, names, sum(f.additions for f in files), sum(f.deletions for f in files))

    def get_changed_files(self) -> tuple[ChangedFile, ...]:
        names = tuple(p for p in self.repo.git.diff("--cached", "--name-only", "-z").split("\0") if p)
        stats: dict[str, tuple[int, int]] = {}
        for line in self.repo.git.diff("--cached", "--numstat").splitlines():
            fields = line.split("\t", 2)
            if len(fields) == 3:
                stats[fields[2]] = (int(fields[0]) if fields[0].isdigit() else 0,
                                    int(fields[1]) if fields[1].isdigit() else 0)
        return tuple(ChangedFile(name, "modified", *stats.get(name, (0, 0))) for name in names)
