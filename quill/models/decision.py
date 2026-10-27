from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommitMessage:
    subject: str
    body: str = ""
    provider: str = "Gemini"

    @property
    def text(self) -> str:
        return f"{self.subject}\n\n{self.body}" if self.body else self.subject
