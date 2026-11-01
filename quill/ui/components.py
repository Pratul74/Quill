# quill/ui/components.py
from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from quill.ui.console import console
from quill.ui.preview import TYPE_COLORS

KINDS = {
    "success": ("✓", "success"),
    "error": ("✕", "error"),
    "warning": ("!", "warning"),
    "info": ("●", "info"),
}

ACTIONS = {
    "y": ("Y", "Commit", "bold black on green"),
    "e": ("E", "Edit", "bold black on #a47dff"),
    "r": ("R", "Regenerate", "bold black on yellow"),
    "n": ("N", "Cancel", "bold white on bright_black"),
}


def section(title: str) -> Rule:
    return Rule(Text(f" {title} ", style="info.bold"), style="bright_black", characters="─")


def status_line(kind: str, message: object) -> Text:
    icon, style = KINDS[kind]
    return Text.assemble((f"{icon} ", f"{style}.bold"), (str(message), "white"), overflow="fold")


def notice_panel(kind: str, title: str, message: object, hint: str | None = None) -> Panel:
    icon, style = KINDS[kind]
    body = Text(str(message), style="white", overflow="fold")
    if hint:
        body.append("\n")
        body.append(hint, style="bright_black")
    return Panel(
        body,
        title=Text.assemble((f"{icon} ", f"{style}.bold"), (title, "bold white")),
        title_align="left",
        border_style=style,
        box=box.ROUNDED,
        padding=(0, 2),
    )


def _confidence_bar(value: float, width: int = 20) -> Text:
    value = max(0.0, min(1.0, value))
    filled = round(value * width)
    style = "success" if value >= 0.75 else "warning" if value >= 0.5 else "error"
    return Text.assemble(("█" * filled, style), ("░" * (width - filled), "bright_black"))


def analysis_panel(report) -> Panel:
    kind = str(getattr(report.commit_type, "value", report.commit_type))
    head = Text(f" {kind.upper()} ", style=f"bold black on {TYPE_COLORS.get(kind.lower(), 'grey70')}")
    if report.scope:
        head.append(f"  ({report.scope})", style="info.bold")

    confidence = _confidence_bar(report.confidence)
    confidence.append(f"  {report.confidence:.0%}", style="bold white")

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="subtitle", no_wrap=True)
    grid.add_column(ratio=1)
    grid.add_row("TYPE", head)
    grid.add_row("CONFIDENCE", confidence)
    if report.reasons:
        reasons = Text("\n").join(
            Text.assemble(("› ", "info"), (str(reason), "white")) for reason in report.reasons
        )
        grid.add_row("WHY", reasons)

    return Panel(
        grid,
        title=Text.assemble(("◈ ", "info"), ("ANALYSIS", "bold white")),
        title_align="left",
        border_style="bright_black",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def action_bar(keys: str) -> Text:
    bar = Text("  ")
    for key in keys:
        letter, label, style = ACTIONS[key]
        bar.append(f" {letter} ", style=style)
        bar.append(f" {label}   ", style="white")
    return bar


def ask_action(keys: str, default: str = "n") -> str:
    console.print()
    console.print(action_bar(keys))
    answer = Prompt.ask(
        Text.assemble(("❯ ", "info.bold"), ("Choose", "white")),
        choices=list(keys),
        default=default,
        console=console,
        show_choices=False,
        case_sensitive=False,
    )
    return answer.lower()


def commit_success_panel(sha: str, branch: object, message: str) -> Panel:
    lines = message.strip().splitlines()
    subject = lines[0] if lines else ""

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="subtitle", no_wrap=True)
    grid.add_column(ratio=1)
    grid.add_row("COMMIT", Text(sha[:7], style="info.bold"))
    grid.add_row("BRANCH", Text(str(branch), style="info"))
    grid.add_row("MESSAGE", Text(subject, style="bold white", overflow="fold"))

    return Panel(
        grid,
        title=Text.assemble(("✓ ", "success.bold"), ("COMMIT CREATED", "bold white")),
        title_align="left",
        border_style="success",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def setup_header() -> Panel:
    body = Text.assemble(
        ("Let's get Quill ready.\n", "bold white"),
        ("Pick a provider and tweak the defaults. You can change anything later in config.toml.", "bright_black"),
    )
    return Panel(
        body,
        title=Text.assemble(("✦ ", "info"), ("FIRST-TIME SETUP", "bold white")),
        title_align="left",
        border_style="border",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def step_label(index: int, label: str) -> Text:
    return Text.assemble(("\n", ""), (f" {index} ", "bold black on #a47dff"), (f"  {label}", "bold white"))


def setup_summary(rows: list[tuple[str, str]]) -> Panel:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="subtitle", no_wrap=True)
    grid.add_column(ratio=1)
    for label, value in rows:
        grid.add_row(label, Text(value, style="white", overflow="fold"))
    return Panel(
        grid,
        title=Text.assemble(("✓ ", "success.bold"), ("YOU'RE ALL SET", "bold white")),
        title_align="left",
        border_style="success",
        box=box.ROUNDED,
        padding=(1, 2),
    )