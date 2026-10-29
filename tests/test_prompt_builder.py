from pathlib import Path

from quill.models.analysis import AnalysisReport
from quill.models.change import ChangedFile
from quill.models.diff import DiffSnapshot
from quill.models.processed_patch import ProcessedPatch
from quill.models.repository import RepositoryInfo
from quill.models.snapshot import RepositorySnapshot
from quill.models.status import GitStatus
from quill.prompt.builder import PromptBuilder


def test_prompt_contains_repository_analysis_files_and_patch() -> None:
    snapshot = RepositorySnapshot(RepositoryInfo("demo", Path("."), "main", "abc"),
        GitStatus(True, False, False, False, False, True), (ChangedFile("src/a.py", "modified"),),
        DiffSnapshot("diff", ("src/a.py",), 1, 0))
    prompt = PromptBuilder().build(snapshot, AnalysisReport("feat", "src", 0.7, ("added",), ((".py", 1),)),
                                   (ProcessedPatch("src/a.py", "@@ -0,0 +1 @@\n+value = 1"),))
    assert "Repository Information" in prompt
    assert "Type: feat" in prompt
    assert "src/a.py" in prompt
    assert "+value = 1" in prompt
