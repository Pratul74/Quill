<!-- markdownlint-disable MD033 -->

<h1 align="center">
  <img src="assets/logo.png" width="48" alt="Quill Logo">
  Quill
</h1>

<!-- markdownlint-enable MD033 -->

Quill analyzes staged Git changes and drafts a detailed Conventional Commit message. A LangGraph agent coordinates repository analysis, language-neutral patch preparation, message generation, and a review-and-revision pass. LangChain chat integrations connect Gemini, OpenAI, Anthropic, and Ollama. Quill can create the Git commit after you review and confirm the message.

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

Quill reads preferences and secrets from its per-user configuration directory. Project `.env` files are never loaded. On first interactive use, Quill asks you to choose Gemini, OpenAI, Anthropic, or Ollama; choose a model ID; and set the output language, commit style, and commit confirmation preference. Quill writes the defaults to `config.toml` and the selected provider's key to `secrets.toml`. For non-interactive use, configure these files or use environment variables.

| Platform | Configuration directory |
| --- | --- |
| Linux | `~/.config/quill/` (or `$XDG_CONFIG_HOME/quill/`) |
| macOS | `~/Library/Application Support/quill/` |
| Windows | `%APPDATA%/quill/` |

Put provider credentials in `secrets.toml`, for example:

```toml
google_api_key = "your-gemini-key"
openai_api_key = "your-openai-key"
anthropic_api_key = "your-anthropic-key"
```

Put preferences in `config.toml`:

```toml
default_model = "gemini"
commit_style = "conventional"
language = "en"
confirm_before_commit = true
gemini_model = "gemini-3.5-flash-lite"
openai_model = "gpt-4o-mini"
anthropic_model = "claude-haiku-4-5-20251001"
ollama_model = "qwen3:8b"
ollama_host = "http://localhost:11434"
retries = 2
```

Quill supports Gemini, OpenAI, Anthropic, and Ollama. Model IDs are configurable in `config.toml` or with `QUILL_GEMINI_MODEL`, `QUILL_OPENAI_MODEL`, `QUILL_ANTHROPIC_MODEL`, and `QUILL_OLLAMA_MODEL`. Select the provider with `default_model` or `QUILL_DEFAULT_MODEL`. API keys are read from `secrets.toml`; standard `GOOGLE_API_KEY`, `OPENAI_API_KEY`, and `ANTHROPIC_API_KEY` variables (and their `QUILL_` prefixed equivalents) override those values. Transient cloud-provider failures can fall back to Ollama.

Projects may contain a `.quill.toml` for preferences such as `language`, `commit_style`, `editor`, `default_model`, or `confirm_before_commit`. It cannot contain secrets; attempts to add secret fields are reported as invalid configuration.

Optional settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `OLLAMA_MODEL` | `qwen3:8b` | Local fallback model |

On Windows, Quill can download and launch Ollama's official installer if Ollama is missing, then start its local service. The installer window is shown so the user can complete setup. On other platforms, install Ollama from its [official download page](https://ollama.com/download). Quill automatically downloads the configured model the first time it is used, so users do not need to run `ollama pull` themselves.

## Use

Stage the changes to describe, then run `quill` inside a repository:

```powershell
git add .
quill
```

Download an Ollama model directly from the Quill terminal. If no model ID is given, Quill uses the configured `ollama_model`:

```powershell
quill pull
quill pull qwen3:8b
```

Quill displays repository information, deterministic analysis hints, and the generated message, then offers commit, edit, regenerate, or cancel. Edit opens the message in your configured text editor, including its full multiline body. Scopes use the deepest shared changed-file directory (so `quill/git/diff.py` yields `git`). Patch analysis works across languages such as Python, JavaScript, and Java. A commit is created only after you choose commit and confirm. Options:

```powershell
quill --path ..\another-repository
quill --edit
quill --commit
```

Only staged content is sent to the model. Generated lockfiles are listed but excluded from the patch prompt. Review the output before committing.
