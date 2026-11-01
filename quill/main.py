import json
import os
import typer
import click
from git import GitCommandError
from rich.prompt import Confirm, Prompt
from rich.rule import Rule

from quill.config.exceptions import ConfigError
from quill.config.manager import ConfigManager
from quill.config import paths
from quill.config.init import initialize_config
from quill.llm.errors import ProviderError
from quill.llm.ollama import pull_model
from quill.services.ai import generate_commit_message
from quill.services.git import inspect_repository
from quill.ui.banner import show_banner
from quill.ui.console import console
from quill.ui.panels import changes_panel, repository_panel
from quill.ui.preview import message_panel

app = typer.Typer(help="Quill — thoughtful, AI-powered Git commit messages", no_args_is_help=False, add_completion=False)


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
    console.print(show_banner())
    _first_run_setup()
    try:
        repo, snapshot = inspect_repository(path)
    except (ValueError, GitCommandError) as exc:
        console.print(f"\n[error]✕ {exc}[/error]")
        raise typer.Exit(1) from exc

    try:
        settings = ConfigManager().load(project_root=snapshot.info.root_path)
    except ConfigError as exc:
        console.print(f"\n[error]✕ {exc}[/error]")
        raise typer.Exit(1) from exc

    console.print(repository_panel(snapshot))
    console.print(changes_panel(snapshot))
    from quill.analyzer.engine import AnalyzerEngine
    report = AnalyzerEngine().analyze(snapshot)
    scope = f"({report.scope})" if report.scope else ""
    console.print(f"[info]ANALYSIS[/info]  [bold]{report.commit_type}{scope}[/bold] · {report.confidence:.0%} confidence · {' '.join(report.reasons)}")
    if snapshot.status.has_conflicts:
        console.print("[error]Resolve merge conflicts before generating a commit message.[/error]")
        raise typer.Exit(1)
    if not snapshot.diff.files or not snapshot.diff.text.strip():
        console.print("\n[warning]Stage the changes you want Quill to describe, then run it again.[/warning]")
        raise typer.Exit(1)
    console.print(Rule("[bright_black]READING YOUR CHANGES[/bright_black]", style="bright_black"))
    with console.status("[cyan]Understanding the staged diff…[/cyan]", spinner="dots"):
        try:
            result = generate_commit_message(snapshot, settings)
        except (ProviderError, ConfigError) as exc:
            console.print(f"\n[error]✕ {exc}[/error]")
            raise typer.Exit(1) from exc
    provider = f"{result.provider.value.capitalize()} · local fallback" if result.fallback_used else result.provider.value.capitalize()
    console.print(message_panel(result.message, provider))

    message = result.message
    action = "e" if edit else "y" if create else Prompt.ask("[cyan]Commit? [Y] commit / [E] edit / [R] regenerate / [N] cancel[/cyan]", choices=["y", "e", "r", "n"], default="n").lower()
    while action in ("e", "r"):
        if action == "e":
            edited = click.edit(message, extension=".txt", editor=settings.app.editor)
            if edited is not None:
                message = edited.strip()
            if not message:
                console.print("[warning]The commit message cannot be empty.[/warning]")
                action = Prompt.ask("[cyan]Commit? [Y] commit / [E] edit / [N] cancel[/cyan]", choices=["y", "e", "n"], default="e").lower()
                continue
            action = "y" if create else Prompt.ask("[cyan]Commit? [Y] commit / [N] cancel[/cyan]", choices=["y", "n"], default="n").lower()
            break
        with console.status("[cyan]Regenerating message…[/cyan]", spinner="dots"):
            try:
                result = generate_commit_message(snapshot, settings)
            except (ProviderError, ConfigError) as exc:
                console.print(f"\n[error]✕ {exc}[/error]")
                raise typer.Exit(1) from exc
        message = result.message
        provider = f"{result.provider.value.capitalize()} · local fallback" if result.fallback_used else result.provider.value.capitalize()
        console.print(message_panel(message, provider))
        action = Prompt.ask("[cyan]Commit? [Y] commit / [E] edit / [R] regenerate / [N] cancel[/cyan]", choices=["y", "e", "r", "n"], default="n").lower()
    if action == "y":
        if settings.app.confirm_before_commit and not Confirm.ask("Create this commit?", default=True):
            console.print("[bright_black]No commit created.[/bright_black]")
            raise typer.Exit(0)
        try:
            repo.index.commit(message)
        except (GitCommandError, Exception) as exc:
            console.print(f"[error]Could not create commit: {exc}[/error]")
            raise typer.Exit(1) from exc
        console.print("\n[success]✓ Commit created successfully.[/success]")
    else:
        console.print("\n[bright_black]Nothing committed. Run  quill --commit  to create this commit.[/bright_black]")


@app.command(name="pull")
def pull_ollama_model(model: str | None = typer.Argument(None, help="Ollama model ID to download; defaults to the configured model.")) -> None:
    try:
        settings = ConfigManager().load()
        pull_model(model or settings.llm.ollama_model, settings.llm.ollama_host)
    except (ConfigError, ProviderError) as exc:
        console.print(f"[error]✕ {exc}[/error]")
        raise typer.Exit(1) from exc


def _first_run_setup() -> None:
    directory = paths.config_directory()
    first_run = not (directory / "secrets.toml").exists()
    initialize_config(directory)
    if not first_run or not click.get_text_stream("stdin").isatty():
        return
    console.print("\n[info]First-time setup[/info] Choose a provider and customize any defaults.")
    provider = Prompt.ask("Provider", choices=["gemini", "openai", "anthropic", "ollama"], default="gemini").lower()
    config_file = directory / "config.toml"
    config_text = config_file.read_text(encoding="utf-8")
    model_field, model_default = {
        "gemini": ("gemini_model", "gemini-3.5-flash-lite"),
        "openai": ("openai_model", "gpt-4o-mini"),
        "anthropic": ("anthropic_model", "claude-haiku-4-5-20251001"),
        "ollama": ("ollama_model", "qwen3:8b"),
    }[provider]
    model = Prompt.ask("Model ID", default=model_default).strip() or model_default
    language = Prompt.ask("Output language", default="en").strip() or "en"
    style = Prompt.ask("Commit style", choices=["conventional", "simple"], default="conventional")
    confirm = Confirm.ask("Confirm before creating a commit?", default=True)
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
            "gemini": ("google_api_key", "Google AI API key (https://aistudio.google.com/app/apikey)"),
            "openai": ("openai_api_key", "OpenAI API key (https://platform.openai.com/api-keys)"),
            "anthropic": ("anthropic_api_key", "Anthropic API key (https://console.anthropic.com/settings/keys)"),
        }
        secret_field, prompt = key_prompts[provider]
        api_key = Prompt.ask(prompt, password=True).strip()
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
        console.print("[success]API key saved to Quill's private user configuration.[/success]")
    elif provider != "ollama" and not has_key_in_env:
        console.print(f"[warning]No key entered. Add {secret_field} to secrets.toml before generating messages.[/warning]")
        (directory / "secrets.toml").unlink(missing_ok=True)
    if provider == "ollama":
        console.print("[info]Quill can install Ollama on Windows and will download the selected model automatically when first used.[/info]")


if __name__ == "__main__":
    app()
