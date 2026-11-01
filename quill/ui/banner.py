from rich import box
from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from quill.ui.console import console

GLYPHS = {
    "Q": [
        " ██████╗ ",
        "██╔═══██╗",
        "██║   ██║",
        "██║▄▄ ██║",
        "╚██████╔╝",
        " ╚══▀▀═╝ ",
    ],
    "U": [
        "██╗   ██╗",
        "██║   ██║",
        "██║   ██║",
        "██║   ██║",
        "╚██████╔╝",
        " ╚═════╝ ",
    ],
    "I": [
        "██╗",
        "██║",
        "██║",
        "██║",
        "██║",
        "╚═╝",
    ],
    "L": [
        "██╗     ",
        "██║     ",
        "██║     ",
        "██║     ",
        "███████╗",
        "╚══════╝",
    ],
}

GRADIENT = [f"logo.{i}" for i in range(1, 7)]
NAME = "AI Commit Assistant"
TAGLINE = "Thoughtful commit messages from staged changes."
PADDING_X = 4
PANEL_OVERHEAD = PADDING_X * 2 + 2


def build_logo(word: str = "QUILL") -> list[str]:
    rows = ["".join(GLYPHS[ch][i] for ch in word) for i in range(6)]
    width = max(len(r) for r in rows)
    return [r.ljust(width) for r in rows]


def show_banner() -> RenderableType:
    logo_rows = build_logo()
    content_width = max(len(logo_rows[0]), len(TAGLINE))

    if console.width < content_width + PANEL_OVERHEAD:
        header: list[RenderableType] = [Align.center(Text("QUILL", style="logo"))]
    else:
        header = [
            Align.center(Text(row, style=style, no_wrap=True))
            for row, style in zip(logo_rows, GRADIENT)
        ]

    subtitle = Text(justify="center")
    subtitle.append(NAME, style="title")
    subtitle.append("\n")
    subtitle.append(TAGLINE, style="subtitle")

    panel = Panel(
        Group(*header, Text(""), subtitle),
        box=box.ROUNDED,
        border_style="border",
        padding=(1, PADDING_X),
        expand=False,
    )
    return Align.center(panel)