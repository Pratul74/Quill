from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from quill.models.snapshot import RepositorySnapshot


def repository_panel(snapshot: RepositorySnapshot) -> Panel:
    status = snapshot.status
    state = "[success]● ready[/success]" if status.can_create_messages else "[warning]● needs attention[/warning]"
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bright_black", no_wrap=True)
    table.add_column(style="white")
    table.add_row("REPOSITORY", f"[bold]{snapshot.info.name}[/bold]  [bright_black]{snapshot.info.root_path}[/bright_black]")
    table.add_row("BRANCH", f"[cyan]{snapshot.info.current_branch}[/cyan]  [bright_black]· {snapshot.info.head_commit}[/bright_black]")
    table.add_row("STAGED", f"[bold]{len(snapshot.diff.files)}[/bold] files  [green]+{snapshot.diff.additions}[/green]  [red]-{snapshot.diff.deletions}[/red]    {state}")
    return Panel(table, title="[bold cyan]✦  WORKSPACE[/bold cyan]", border_style="bright_blue", box=box.ROUNDED, padding=(1, 2))


def changes_panel(snapshot: RepositorySnapshot) -> Panel:
    if not snapshot.diff.files:
        content = Text("Nothing staged yet. Use  git add <files>  and run quill again.", style="yellow")
    else:
        table = Table(box=None, show_header=True, header_style="bright_black", expand=True, padding=(0, 1))
        table.add_column("STAGED FILE", style="white")
        table.add_column("CHANGE", justify="right")
        for file in snapshot.changed_files:
            table.add_row(file.path, f"[green]+{file.additions}[/green]  [red]-{file.deletions}[/red]")
        content = table
    return Panel(content, title="[bold]◈  CHANGES IN THIS COMMIT[/bold]", border_style="bright_black", box=box.ROUNDED, padding=(0, 1))
