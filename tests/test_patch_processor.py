from pathlib import Path

from quill.models.change import ChangedFile
from quill.models.diff import DiffSnapshot
from quill.models.repository import RepositoryInfo
from quill.models.snapshot import RepositorySnapshot
from quill.models.status import GitStatus
from quill.prompt.processor import PatchProcessor


def make_snapshot(files: tuple[str, ...], diff: str) -> RepositorySnapshot:
    changes = tuple(ChangedFile(path, "modified") for path in files)
    return RepositorySnapshot(RepositoryInfo("demo", Path("."), "main", "abc123"),
                              GitStatus(True, False, False, False, False, True), changes,
                              DiffSnapshot(diff, files, 0, 0))


def test_removes_file_headers_and_keeps_hunks() -> None:
    raw = "diff --git a/src/a.py b/src/a.py\nindex 1..2 100644\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1 @@\n-old\n+new"
    patch = PatchProcessor().process(make_snapshot(("src/a.py",), raw))[0]
    assert patch.content.startswith("@@")
    assert "diff --git" not in patch.content


def test_omits_lockfile() -> None:
    patch = PatchProcessor().process(make_snapshot(("package-lock.json",), "sensitive bulk diff"))[0]
    assert patch.ignored_generated
    assert not patch.content


def test_truncates_large_file() -> None:
    raw = "diff --git a/a.txt b/a.txt\n@@\n" + "x" * 100
    patch = PatchProcessor(max_file_chars=20).process(make_snapshot(("a.txt",), raw))[0]
    assert patch.truncated
    assert len(patch.content) == 20
