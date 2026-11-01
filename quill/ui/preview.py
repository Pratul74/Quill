import re

from rich import box
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

TYPE_COLORS = {
    "feat": "green", "fix": "red", "docs": "blue", "style": "magenta",
    "refactor": "cyan", "perf": "yellow", "test": "yellow", "build": "grey70",
    "ci": "grey70", "chore": "grey70", "revert": "red",
}

SUBJECT_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s*(?P<desc>.+)$"
)
BULLET_RE = re.compile(r"^\s*[-*•]\s+(.*)$")


def _subject(line: str) -> Text:
    text = Text(overflow="fold")
    match = SUBJECT_RE.match(line)
    kind = match["type"].lower() if match else None

    if match and kind in TYPE_COLORS:
        text.append(f" {kind.upper()} ", style=f"bold black on {TYPE_COLORS[kind]}")
        if match["scope"]:
            text.append(f" ({match['scope']})", style="info.bold")
        if match["bang"]:
            text.append(" !", style="error.bold")
        text.append("  ")
        text.append(match["desc"], style="bold white")
    else:
        text.append(line, style="bold white")
    return text


def _body(lines: list[str]) -> Table:
    grid = Table.grid(padding=(0, 1), expand=True)
    grid.add_column(width=1, no_wrap=True)
    grid.add_column(ratio=1)

    previous_blank = True
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            if not previous_blank:
                grid.add_row("", "")
            previous_blank = True
            continue
        previous_blank = False

        bullet = BULLET_RE.match(line)
        if bullet:
            grid.add_row(Text("•", style="info"), Text(bullet[1], style="white", overflow="fold"))
        else:
            grid.add_row(Text("▏", style="bright_black"), Text(line.strip(), style="white", overflow="fold"))
    return grid


def message_panel(message: str, provider: str) -> Panel:
    lines = message.strip().splitlines() or [""]
    subject, body_lines = lines[0].strip(), lines[1:]
    body_text = [l for l in body_lines if l.strip()]
    length = len(subject)
    meter_style = "success" if length <= 50 else "warning" if length <= 72 else "error"

    parts: list[RenderableType] = [_subject(subject)]
    if body_text:
        parts += [Text(""), _body(body_lines)]

    parts += [
        Text(""),
        Rule(style="bright_black", characters="┈"),
        Text.assemble(
            ("subject ", "subtitle"),
            (f"{length}/72", f"{meter_style}.bold"),
            ("   ·   ", "bright_black"),
            ("body ", "subtitle"),
            (f"{len(body_text)} line{'s' if len(body_text) != 1 else ''}", "white"),
        ),
    ]

    return Panel(
        Group(*parts),
        title=Text.assemble(("✦ ", "success"), ("YOUR COMMIT MESSAGE", "bold white")),
        title_align="left",
        subtitle=Text.assemble(
            ("Generated with ", "bright_black"),
            (provider, "info.bold"),
            (" · review before committing", "bright_black"),
        ),
        subtitle_align="right",
        border_style="success",
        box=box.ROUNDED,
        padding=(1, 2),
    )
