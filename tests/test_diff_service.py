from pathlib import Path

from git import Repo

from quill.git.diff import DiffService


def test_reads_staged_patch_and_file_stats(tmp_path: Path) -> None:
    repo = Repo.init(tmp_path)
    target = tmp_path / "note.txt"
    target.write_text("first\n", encoding="utf-8")
    repo.index.add([str(target)])
    repo.index.commit("initial")
    target.write_text("first\nsecond\n", encoding="utf-8")
    repo.index.add([str(target)])

    service = DiffService(repo)
    snapshot = service.get_staged_diff()

    assert snapshot.files == ("note.txt",)
    assert snapshot.additions == 1
    assert "+second" in snapshot.text
    assert service.get_changed_files()[0].path == "note.txt"
    assert service.get_changed_files()[0].additions == 1
