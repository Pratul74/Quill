import re
from pathlib import PurePosixPath

from quill.models.processed_patch import ProcessedPatch
from quill.models.snapshot import RepositorySnapshot

_GENERATED = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock", "Cargo.lock", "Gemfile.lock"}


class PatchProcessor:
    def __init__(self, max_file_chars: int = 20_000, max_total_chars: int = 60_000) -> None:
        self.max_file_chars = max_file_chars
        self.max_total_chars = max_total_chars

    def process(self, snapshot: RepositorySnapshot) -> tuple[ProcessedPatch, ...]:
        patches: list[ProcessedPatch] = []
        remaining = self.max_total_chars
        for path in snapshot.diff.files:
            if PurePosixPath(path).name in _GENERATED:
                patches.append(ProcessedPatch(path, "", ignored_generated=True))
                continue
            raw = self._file_diff(snapshot.diff.text, path)
            binary = "Binary files " in raw or "GIT binary patch" in raw
            content = "[binary file changed]" if binary else self._clean(raw)
            limit = min(self.max_file_chars, remaining)
            truncated = len(content) > limit
            content = content[:max(limit, 0)]
            remaining -= len(content)
            patches.append(ProcessedPatch(path, content, binary, truncated))
        return tuple(patches)

    @staticmethod
    def _file_diff(diff: str, path: str) -> str:
        pieces = re.split(r"(?=^diff --git )", diff, flags=re.M)
        for piece in pieces:
            if piece.startswith("diff --git ") and (f" b/{path}\n" in piece or f" b/{path}\r\n" in piece):
                return piece
        return ""

    @staticmethod
    def _clean(raw: str) -> str:
        lines = raw.splitlines()
        kept = [line for line in lines if not line.startswith(("diff --git ", "index ", "--- a/", "+++ b/"))]
        text = "\n".join(kept)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()
