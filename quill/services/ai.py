import re
from dotenv import load_dotenv

from quill.analyzer.engine import AnalyzerEngine
from quill.llm.errors import ProviderError
from quill.llm.manager import LLMManager
from quill.models.patch import GenerationResult
from quill.models.snapshot import RepositorySnapshot
from quill.prompt.builder import PromptBuilder
from quill.prompt.processor import PatchProcessor


def _clean_message(value: str) -> str:
    message = value.strip()
    message = re.sub(r"\A```(?:\w+)?\s*|\s*```\Z", "", message, flags=re.IGNORECASE)
    return message.strip()


def generate_commit_message(snapshot: RepositorySnapshot) -> GenerationResult:
    """Build model context from a staged snapshot and generate a commit message."""
    if not snapshot.diff.text.strip():
        raise ProviderError("The staged diff is empty. Stage the changes you want Quill to describe.")

    load_dotenv(snapshot.info.root_path / ".env", override=False)

    report = AnalyzerEngine().analyze(snapshot)
    patches = PatchProcessor().process(snapshot)
    if not any(patch.content for patch in patches):
        raise ProviderError("The staged changes contain no reviewable text after generated files are omitted.")

    prompt = PromptBuilder().build(snapshot, report, patches)
    result = LLMManager().generate(prompt)
    message = _clean_message(result.message)
    if not message:
        raise ProviderError("The model returned an empty commit message.")
    return GenerationResult(message, result.provider, result.fallback_used)
