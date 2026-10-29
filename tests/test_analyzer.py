from pathlib import Path

from quill.analyzer.engine import AnalyzerEngine
from quill.models.change import ChangedFile
from quill.models.diff import DiffSnapshot
from quill.models.repository import RepositoryInfo
from quill.models.snapshot import RepositorySnapshot
from quill.models.status import GitStatus


def snapshot(*paths: str) -> RepositorySnapshot:
    files = tuple(ChangedFile(path, "modified", 2, 0) for path in paths)
    return RepositorySnapshot(RepositoryInfo("demo", Path("."), "main", "abc123"),
                              GitStatus(True, False, False, False, False, True), files,
                              DiffSnapshot("", paths, 2 * len(paths), 0))


def test_docs_only_changes_suggest_docs() -> None:
    assert AnalyzerEngine().analyze(snapshot("README.md")).commit_type == "docs"


def test_workflow_change_suggests_ci() -> None:
    assert AnalyzerEngine().analyze(snapshot(".github/workflows/ci.yml")).commit_type == "ci"


def test_scope_uses_shared_top_level_directory() -> None:
    assert AnalyzerEngine().analyze(snapshot("src/auth/login.py", "src/auth/token.py")).scope == "src"
