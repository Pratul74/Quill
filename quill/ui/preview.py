from rich import box
from rich.panel import Panel
from rich.text import Text


def message_panel(message: str, provider: str) -> Panel:
    return Panel(
        Text(message, style="bold white", overflow="fold"),
        title="[bold green]✦  YOUR COMMIT MESSAGE[/bold green]",
        subtitle=f"[bright_black]Generated with {provider} · review before committing[/bright_black]",
        border_style="green", box=box.ROUNDED, padding=(1, 2),
    )
