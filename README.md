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

Quill reads preferences and secrets from its per-user configuration directory. Project `.env` files are never loaded. Create `config.toml` and `secrets.toml` in the directory below using the examples that follow. The configuration initializer is ready to back a future `quill init` command.

| Platform | Configuration directory |
| --- | --- |
| Linux | `~/.config/quill/` (or `$XDG_CONFIG_HOME/quill/`) |
| macOS | `~/Library/Application Support/quill/` |
| Windows | `%APPDATA%/quill/` |

Put provider credentials in `secrets.toml`, for example:

```toml
google_api_key = "your-key"
openai_api_key = ""
anthropic_api_key = ""
```

Put preferences in `config.toml`:

```toml
default_model = "gemini"
commit_style = "conventional"
language = "en"
confirm_before_commit = true
gemini_model = "gemini-3.5-flash-lite"
ollama_model = "qwen3:8b"
ollama_host = "http://localhost:11434"
retries = 2
```

Quill uses `gemini-3.5-flash-lite` through LangChain's Google GenAI integration, with bounded retries. It falls back to Ollama through LangChain only when Gemini fails temporarily. Existing shell variables such as `GOOGLE_API_KEY`, `OLLAMA_MODEL`, and `OLLAMA_HOST` continue to work and override global file values. `QUILL_DEFAULT_MODEL`, `QUILL_GEMINI_MODEL`, `QUILL_OLLAMA_MODEL`, and `QUILL_OLLAMA_HOST` also accept overrides. Set `QUILL_DEFAULT_MODEL=ollama` to use Ollama as the primary model.

Projects may contain a `.quill.toml` for preferences such as `language`, `commit_style`, `editor`, `default_model`, or `confirm_before_commit`. It cannot contain secrets; attempts to add secret fields are reported as invalid configuration.

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
