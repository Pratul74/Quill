from collections import Counter
from pathlib import PurePosixPath

from quill.models.analysis import AnalysisReport
from quill.models.snapshot import RepositorySnapshot


class AnalyzerEngine:
    """Infer Conventional Commit hints without using a language model."""

    def analyze(self, snapshot: RepositorySnapshot) -> AnalysisReport:
        paths = [PurePosixPath(item.path.replace("\\", "/")) for item in snapshot.changed_files]
        counts = Counter(path.suffix.lower() or path.name.lower() for path in paths)
        names = [str(path).lower() for path in paths]
        if names and all(path.endswith((".md", ".rst", ".txt")) or path.endswith("readme") for path in names):
            kind, reason = "docs", "Only documentation files changed."
        elif any(path == "dockerfile" or "/dockerfile" in path for path in names) or any("pyproject.toml" in path or "setup.py" in path for path in names):
            kind, reason = "build", "Build or packaging configuration changed."
        elif any(path.startswith(".github/workflows/") for path in names):
            kind, reason = "ci", "Continuous integration workflow changed."
        elif any(item.additions for item in snapshot.changed_files) and not any(item.deletions for item in snapshot.changed_files):
            kind, reason = "feat", "Changes primarily add content."
        elif any(item.deletions for item in snapshot.changed_files):
            kind, reason = "fix", "Changes include removals or replacements."
        else:
            kind, reason = "chore", "No stronger deterministic commit type signal was found."
        parents = [path.parent.as_posix() for path in paths if path.parent.as_posix() not in ("", ".")]
        scope = parents[0].split("/")[1] if parents and len(set(p.split("/")[1] for p in parents)) == 1 else None
        return AnalysisReport(kind, scope, 0.8 if kind in {"docs", "build", "ci"} else 0.55,
                              (reason,), tuple(sorted(counts.items())))
