import json
import os
from typing import NoReturn

import click
import typer
from git import GitCommandError
from rich.prompt import Confirm, Prompt
from rich.text import Text

from quill.config import paths
from quill.config.exceptions import ConfigError
from quill.config.init import initialize_config
from quill.config.manager import ConfigManager
from quill.llm.errors import ProviderError
from quill.llm.ollama import pull_model
from quill.services.ai import generate_commit_message
from quill.services.git import inspect_repository
from quill.ui.banner import show_banner
from quill.ui.components import (
    analysis_panel,
    ask_action,
    commit_success_panel,
    notice_panel,
    section,
    setup_header,
    setup_summary,
    status_line,
    step_label,
    prompt_label,
)
from quill.ui.console import console
from quill.ui.panels import changes_panel, repository_panel
from quill.ui.preview import message_panel

app = typer.Typer(help="Quill — thoughtful, AI-powered Git commit messages", no_args_is_help=False, add_completion=False)


def _fail(message: object, title: str = "ERROR", hint: str | None = None) -> NoReturn:
    console.print()
    console.print(notice_panel("error", title, message, hint))
    raise typer.Exit(1)


def _provider_label(result) -> str:
    name = result.provider.value.capitalize()
    return f"{name} · local fallback" if result.fallback_used else name


def _generate(snapshot, settings, label: str):
    error: Exception
    with console.status(Text(label, style="info"), spinner="dots12"):
        try:
            return generate_commit_message(snapshot, settings)
        except (ProviderError, ConfigError) as exc:
            error = exc
    _fail(error)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    path: str = typer.Option(".", "--path", "-p", help="Repository directory to inspect."),
    create: bool = typer.Option(False, "--commit", help="Commit after reviewing the message."),
    edit: bool = typer.Option(False, "--edit", help="Edit the generated message before continuing."),
) -> None:
    if ctx.invoked_subcommand is None:
        commit(path, create, edit)


@app.command()
def commit(
    path: str = typer.Option(".", "--path", "-p", help="Repository directory to inspect."),
    create: bool = typer.Option(False, "--commit", help="Create a Git commit after reviewing the message."),
    edit: bool = typer.Option(False, "--edit", help="Edit the generated message before continuing."),
) -> None:
    console.print()
    console.print(show_banner())
    _first_run_setup()

    try:
        repo, snapshot = inspect_repository(path)
    except (ValueError, GitCommandError) as exc:
        _fail(exc, "REPOSITORY ERROR")

    try:
        settings = ConfigManager().load(project_root=snapshot.info.root_path)
    except ConfigError as exc:
        _fail(exc, "CONFIG ERROR")

    console.print(repository_panel(snapshot))
    console.print(changes_panel(snapshot))

    if snapshot.status.has_conflicts:
        _fail("Merge conflicts detected.", "CONFLICTS", "Resolve them, then run quill again.")
    if not snapshot.diff.files or not snapshot.diff.text.strip():
        console.print(
            notice_panel(
                "warning", "NOTHING STAGED",
                "Stage the changes you want Quill to describe, then run it again.",
            )
        )
        raise typer.Exit(1)

    from quill.analyzer.engine import AnalyzerEngine

    console.print(analysis_panel(AnalyzerEngine().analyze(snapshot)))

    console.print()
    console.print(section("READING YOUR CHANGES"))
    result = _generate(snapshot, settings, "Understanding the staged diff…")
    message = result.message
    console.print(message_panel(message, _provider_label(result)))

    action = "e" if edit else "y" if create else ask_action("yern")
    while action in ("e", "r"):
        if action == "e":
            edited = click.edit(message, extension=".txt", editor=settings.app.editor)
            if edited is not None:
                message = edited.strip()
            if not message:
                console.print(notice_panel("warning", "EMPTY MESSAGE", "The commit message cannot be empty."))
                action = ask_action("en", default="e")
                continue
            action = "y" if create else ask_action("yn")
            break

        result = _generate(snapshot, settings, "Regenerating message…")
        message = result.message
        console.print(message_panel(message, _provider_label(result)))
        action = ask_action("yern")

    if action != "y":
        console.print()
        console.print(
            Text.assemble(
                ("Nothing committed. Run", "muted"),
                ("quill --commit", "info.bold"),
                (" to create this commit.", "muted"),
            )
        )
        return

    if settings.app.confirm_before_commit and not Confirm.ask(
        prompt_label("Create this commit?"), default=True, console=console
    ):
        console.print(Text("No commit created.", style="muted"))
        raise typer.Exit(0)

    try:
        created = repo.index.commit(message)
    except Exception as exc:
        _fail(exc, "COMMIT FAILED")
    console.print()
    console.print(commit_success_panel(created.hexsha, snapshot.info.current_branch, message))


@app.command(name="pull")
def pull_ollama_model(
    model: str | None = typer.Argument(None, help="Ollama model ID to download; defaults to the configured model."),
) -> None:
    try:
        settings = ConfigManager().load()
        target = model or settings.llm.ollama_model
        console.print(section(f"PULLING {target}"))
        pull_model(target, settings.llm.ollama_host)
    except (ConfigError, ProviderError) as exc:
        _fail(exc, "PULL FAILED")


def _first_run_setup() -> None:
    directory = paths.config_directory()
    setup_marker = directory / ".setup_done"
    first_run = not (setup_marker.exists() or (directory / "secrets.toml").exists())
    initialize_config(directory)
    if not first_run or not click.get_text_stream("stdin").isatty():
        return

    def ask(label: str, **kwargs) -> str:
        return Prompt.ask(prompt_label(label), console=console, **kwargs)

    console.print(setup_header())

    console.print(step_label(1, "Provider"))
    provider = ask("Provider", choices=["gemini", "openai", "anthropic", "ollama"], default="gemini").lower()

    config_file = directory / "config.toml"
    config_text = config_file.read_text(encoding="utf-8")
    model_field, model_default = {
        "gemini": ("gemini_model", "gemini-3.5-flash-lite"),
        "openai": ("openai_model", "gpt-4o-mini"),
        "anthropic": ("anthropic_model", "claude-haiku-4-5-20251001"),
        "ollama": ("ollama_model", "qwen3:8b"),
    }[provider]

    console.print(step_label(2, "Model"))
    model = ask("Model ID", default=model_default).strip() or model_default

    console.print(step_label(3, "Language"))
    language = ask("Output language", default="en").strip() or "en"

    console.print(step_label(4, "Commit style"))
    style = ask("Commit style", choices=["conventional", "simple"], default="conventional")

    console.print(step_label(5, "Safety"))
    confirm = Confirm.ask(
        prompt_label("Confirm before creating a commit?"),
        default=True, console=console,
    )

    replacements = {
        'default_model = "gemini"': f'default_model = "{provider}"',
        f'{model_field} = "{model_default}"': f'{model_field} = {json.dumps(model)}',
        'language = "en"': f'language = {json.dumps(language)}',
        'commit_style = "conventional"': f'commit_style = {json.dumps(style)}',
        'confirm_before_commit = true': f'confirm_before_commit = {str(confirm).lower()}',
    }
    for old, new in replacements.items():
        config_text = config_text.replace(old, new)
    config_file.write_text(config_text, encoding="utf-8")

    api_key = ""
    has_key_in_env = {
        "gemini": bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("QUILL_GOOGLE_API_KEY")),
        "openai": bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("QUILL_OPENAI_API_KEY")),
        "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("QUILL_ANTHROPIC_API_KEY")),
        "ollama": True,
    }[provider]

    if provider != "ollama" and not has_key_in_env:
        key_prompts = {
            "gemini": ("google_api_key", "Google AI API key", "https://aistudio.google.com/app/apikey"),
            "openai": ("openai_api_key", "OpenAI API key", "https://platform.openai.com/api-keys"),
            "anthropic": ("anthropic_api_key", "Anthropic API key", "https://console.anthropic.com/settings/keys"),
        }
        secret_field, label, url = key_prompts[provider]
        console.print(step_label(6, "API key"))
        console.print(Text.assemble(("  Get one at ", "muted"), (url, "link")))
        api_key = ask(label, password=True).strip()

    if api_key:
        secret_file = directory / "secrets.toml"
        secret_values = {"google_api_key": "", "openai_api_key": "", "anthropic_api_key": ""}
        secret_values[secret_field] = api_key
        secret_file.write_text(
            "".join(f"{field} = {json.dumps(value)}\n" for field, value in secret_values.items()),
            encoding="utf-8",
        )
        try:
            os.chmod(secret_file, 0o600)
        except OSError:
            pass
        console.print()
        console.print(status_line("success", "API key saved to Quill's private user configuration."))
    elif provider != "ollama" and not has_key_in_env:
        console.print()
        console.print(status_line("warning", f"No key entered. Add {secret_field} to secrets.toml before generating messages."))

    setup_marker.write_text("done\n", encoding="utf-8")

    console.print()
    console.print(
        setup_summary([
            ("PROVIDER", provider),
            ("MODEL", model),
            ("LANGUAGE", language),
            ("STYLE", style),
            ("CONFIRM", "yes" if confirm else "no"),
        ])
    )
    if provider == "ollama":
        console.print(status_line("info", "Quill can install Ollama on Windows and will download the selected model automatically on first use."))


if __name__ == "__main__":
    app()
