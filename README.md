# Quill ✦

Quill is a small terminal companion that reads your **staged Git diff** and drafts a Conventional Commit message. It uses Google Gemini first, then automatically switches to a local Ollama model if Gemini returns a rate limit response.

## Install

```bash
python -m pip install -e .
```

## Configure Gemini

Set `GEMINI_API_KEY` in your environment. Optional settings:

- `GEMINI_MODEL` (default: `gemini-2.5-flash`)
- `OLLAMA_HOST` (default: `http://localhost:11434`)
- `OLLAMA_MODEL` (default: `llama3.2`)

Install and start Ollama, then pull a model (for example `ollama pull llama3.2`) to enable local fallback when Gemini rate limits you.

## Use

Stage the changes you want to describe, then run `quill` from anywhere inside the repository. Quill shows the repository, branch, staged file summary, and generated message. It never commits without an explicit `--commit` option and confirmation.

```bash
git add src/
quill
quill --edit              # type an edited message interactively
quill --commit            # review, confirm, and create the commit
quill --path ../project   # choose a repository directory
```

Only staged changes are sent to the selected model. Review the generated message before using it.
