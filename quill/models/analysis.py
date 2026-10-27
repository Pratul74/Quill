from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    commit_type: str
    scope: str | None
    confidence: float
    reasons: tuple[str, ...]
    statistics: tuple[tuple[str, int], ...]
