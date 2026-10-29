from pathlib import Path

import pytest
from git import Repo

from quill.git.repository import Repository


def test_detects_repository_root(tmp_path: Path) -> None:
    Repo.init(tmp_path)
    nested = tmp_path / "child"
    nested.mkdir()
    assert Repository(nested).root == tmp_path.resolve()


def test_rejects_non_repository(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not inside a Git repository"):
        Repository(tmp_path)
