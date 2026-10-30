<!-- markdownlint-disable MD033 -->

<h1 align="center">
  <img src="assets/logo.png" width="48" alt="Quill Logo">
  Quill
</h1>

<!-- markdownlint-enable MD033 -->

Quill analyzes staged Git changes and drafts a detailed Conventional Commit message. A LangGraph agent coordinates repository analysis, language-neutral patch preparation, message generation, and a review-and-revision pass. LangChain chat integrations connect Gemini and Ollama; no provider SDK is called directly. Quill can create the Git commit after you review and confirm the message.

## Install

Requires Python 3.12 or newer.

```powershell
python -m pip install -e .
```

For development tools:

```powershell
python -m pip install -e ".[dev]"
pytest
```

## Configure

Set `GOOGLE_API_KEY` in the environment or in a `.env` file at the repository root to use Gemini. Quill uses `gemini-3.5-flash-lite` through LangChain's Google GenAI integration, with bounded retries. It falls back to Ollama through LangChain only when Gemini fails; missing keys and other configuration errors are reported directly.

Optional settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `OLLAMA_MODEL` | `qwen3:8b` | Local fallback model |

Ollama fallback requires a running local server and the selected model pulled in advance.

## Use

Stage the changes to describe, then run `quill` inside a repository:

```powershell
git add .
quill
```

Quill displays repository information, deterministic analysis hints, and the generated message, then offers commit, edit, regenerate, or cancel. Edit opens the message in your configured text editor, including its full multiline body. Scopes use the deepest shared changed-file directory (so `quill/git/diff.py` yields `git`). Patch analysis works across languages such as Python, JavaScript, and Java. A commit is created only after you choose commit and confirm. Options:

```powershell
quill --path ..\another-repository
quill --edit
quill --commit
```

Only staged content is sent to the model. Generated lockfiles are listed but excluded from the patch prompt. Review the output before committing.
