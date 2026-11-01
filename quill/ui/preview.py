import re

from rich import box
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from quill.ui.theme import TYPE_COLORS, type_badge

SUBJECT_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s*(?P<desc>.+)$"
)
BULLET_RE = re.compile(r"^\s*[-*•]\s+(.*)$")

SUBJECT_IDEAL = 50
SUBJECT_MAX = 72


def _subject(line: str) -> Text:
    text = Text(overflow="fold")
    match = SUBJECT_RE.match(line)
    kind = match["type"].lower() if match else None

    if match and kind in TYPE_COLORS:
        text.append(f" {kind.upper()} ", style=type_badge(kind))
        if match["scope"]:
            text.append(f" ({match['scope']})", style="info.bold")
        if match["bang"]:
            text.append(" !", style="error.bold")
        text.append("  ")
        text.append(match["desc"], style="title")
    else:
        text.append(line, style="title")
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
            grid.add_row(Text("•", style="info"), Text(bullet[1], style="text", overflow="fold"))
        else:
            grid.add_row(Text("▏", style="faint"), Text(line.strip(), style="text", overflow="fold"))
    return grid


def message_panel(message: str, provider: str) -> Panel:
    lines = message.strip().splitlines() or [""]
    subject, body_lines = lines[0].strip(), lines[1:]
    body_count = sum(1 for line in body_lines if line.strip())
    length = len(subject)
    meter = "success" if length <= SUBJECT_IDEAL else "warning" if length <= SUBJECT_MAX else "error"

    parts: list[RenderableType] = [_subject(subject)]
    if body_count:
        parts += [Text(""), _body(body_lines)]

    parts += [
        Text(""),
        Rule(style="faint", characters="┈"),
        Text.assemble(
            ("subject ", "subtitle"),
            (f"{length}/{SUBJECT_MAX}", f"{meter}.bold"),
            ("   ·   ", "faint"),
            ("body ", "subtitle"),
            (f"{body_count} line{'s' if body_count != 1 else ''}", "text"),
        ),
    ]

    return Panel(
        Group(*parts),
        title=Text.assemble(("✦ ", "success"), ("YOUR COMMIT MESSAGE", "title")),
        title_align="left",
        subtitle=Text.assemble(
            ("Generated with ", "muted"),
            (provider, "info.bold"),
            (" · review before committing", "muted"),
        ),
        subtitle_align="right",
        border_style="success",
        box=box.ROUNDED,
        padding=(1, 2),
    )