import typer
from git import GitCommandError
from rich.prompt import Confirm, Prompt
from rich.rule import Rule

from quill.llm.errors import ProviderError
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
    """Generate a Conventional Commit message from staged changes."""
    console.print(show_banner())
    try:
        repo, snapshot = inspect_repository(path)
    except (ValueError, GitCommandError) as exc:
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
            result = generate_commit_message(snapshot)
        except ProviderError as exc:
            console.print(f"\n[error]✕ {exc}[/error]")
            raise typer.Exit(1) from exc
    provider = "Ollama · local fallback" if result.fallback_used else "Gemini"
    console.print(message_panel(result.message, provider))

    message = result.message
    action = "e" if edit else "y" if create else Prompt.ask("[cyan]Commit? [Y] commit / [E] edit / [R] regenerate / [N] cancel[/cyan]", choices=["y", "e", "r", "n"], default="n").lower()
    while action in ("e", "r"):
        if action == "e":
            message = Prompt.ask("[cyan]Commit message[/cyan]", default=message)
            action = "y" if create else Prompt.ask("[cyan]Commit? [Y] commit / [N] cancel[/cyan]", choices=["y", "n"], default="n").lower()
            break
        with console.status("[cyan]Regenerating message…[/cyan]", spinner="dots"):
            try:
                result = generate_commit_message(snapshot)
            except ProviderError as exc:
                console.print(f"\n[error]✕ {exc}[/error]")
                raise typer.Exit(1) from exc
        message = result.message
        console.print(message_panel(message, "Ollama · local fallback" if result.fallback_used else "Gemini"))
        action = Prompt.ask("[cyan]Commit? [Y] commit / [E] edit / [R] regenerate / [N] cancel[/cyan]", choices=["y", "e", "r", "n"], default="n").lower()
    if action == "y":
        if not Confirm.ask("Create this commit?", default=True):
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


if __name__ == "__main__":
    app()
